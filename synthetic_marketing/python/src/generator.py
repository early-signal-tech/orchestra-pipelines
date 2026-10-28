"""
DLT-Based Synthetic Marketing Data Generator

Uses dlt (data load tool) for robust, production-ready data pipelines.

Architecture:
- 6 resources (one per table): sessions, touchpoints, conversions, campaigns, creatives, metadata
- 1 unified pipeline: Ensures consistency and transactional loading
- Automatic batching: 1K rows per file via dlt's built-in chunking
- State management: dlt handles metadata persistence automatically
- Schema evolution: dlt auto-detects and migrates schema changes

Install: pip install dlt[parquet,filesystem]

Benefits over vanilla approach:
✅ Built-in state management (no manual metadata tracking)
✅ Automatic schema evolution
✅ Transactional loading (all-or-nothing)
✅ Retry logic and error handling
✅ Native support for S3, BigQuery, Snowflake, etc.
✅ Automatic data validation
✅ Load metrics and monitoring
"""

import os
from datetime import date, datetime, time, timedelta
from typing import Iterator, Dict, Any, List
from pathlib import Path
import yaml
import numpy as np
import dlt
import pendulum
from dotenv import load_dotenv

# Import filesystem destination (compatible with different dlt versions)
try:
    from dlt.destinations import filesystem
except ImportError:
    # Fallback for older dlt versions
    from dlt.destinations.filesystem import filesystem
# Load environment variables
load_dotenv()

# Configuration
LOCAL_MODE = os.getenv("LOCAL_MODE", "false").lower() == "true"
LOCAL_OUTPUT_DIR = Path("./data/output")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = "marketing"
CONFIG_PATH = "config.yaml"


def _linked(field: str):
    """Value of an AWS_S3__<connection>__<field> variable that Orchestra exports from a linked connection."""
    return next((v for k, v in os.environ.items() if k.startswith("AWS_S3__") and k.endswith("__AWS_" + field)), None)


# ============================================================
# REALISTIC DISTRIBUTION CONSTANTS
# ============================================================

# Channel-specific performance profiles (based on industry benchmarks)
CHANNEL_PROFILES = {
    "linkedin": {"ctr_mean": 0.006, "ctr_std": 0.002, "cpc_mean": 5.0, "cpc_std": 1.5, "conv_rate": 0.04},
    "google_ads": {"ctr_mean": 0.035, "ctr_std": 0.015, "cpc_mean": 2.5, "cpc_std": 1.0, "conv_rate": 0.08},
    "meta": {"ctr_mean": 0.012, "ctr_std": 0.004, "cpc_mean": 1.2, "cpc_std": 0.4, "conv_rate": 0.06},
    "tiktok": {"ctr_mean": 0.018, "ctr_std": 0.006, "cpc_mean": 0.8, "cpc_std": 0.3, "conv_rate": 0.05},
    "twitter": {"ctr_mean": 0.008, "ctr_std": 0.003, "cpc_mean": 1.5, "cpc_std": 0.5, "conv_rate": 0.04},
    "pinterest": {"ctr_mean": 0.015, "ctr_std": 0.005, "cpc_mean": 1.0, "cpc_std": 0.4, "conv_rate": 0.07},
    "snapchat": {"ctr_mean": 0.010, "ctr_std": 0.004, "cpc_mean": 0.9, "cpc_std": 0.3, "conv_rate": 0.03},
    "reddit": {"ctr_mean": 0.007, "ctr_std": 0.003, "cpc_mean": 0.7, "cpc_std": 0.3, "conv_rate": 0.03},
}

# Device type impact on user behavior
DEVICE_MODIFIERS = {
    "mobile": {"session_duration": 0.7, "pages": 0.6, "conv_rate": 0.85},
    "desktop": {"session_duration": 1.3, "pages": 1.4, "conv_rate": 1.15},
    "tablet": {"session_duration": 1.1, "pages": 1.2, "conv_rate": 1.0},
}

# Country impact on costs and conversion
COUNTRY_MODIFIERS = {
    "us": {"cpc": 1.2, "conv_rate": 1.1},
    "uk": {"cpc": 1.1, "conv_rate": 1.0},
    "de": {"cpc": 1.0, "conv_rate": 0.95},
    "es": {"cpc": 0.8, "conv_rate": 0.85},
    "fr": {"cpc": 0.9, "conv_rate": 0.9},
}

# Creative type performance multipliers
CREATIVE_TYPE_MULTIPLIERS = {
    # Video content - generally higher engagement
    "social_feed_video": {"ctr": 1.3, "engagement": 1.4},
    "video_preroll": {"ctr": 0.9, "engagement": 1.1},
    "reels": {"ctr": 1.5, "engagement": 1.6},
    "in_feed_video": {"ctr": 1.4, "engagement": 1.5},
    "video_ads": {"ctr": 1.2, "engagement": 1.3},
    "video_pin": {"ctr": 1.3, "engagement": 1.4},
    "video_ad": {"ctr": 1.2, "engagement": 1.3},
    # Static/image content - baseline
    "social_feed_image": {"ctr": 1.0, "engagement": 1.0},
    "display_banner": {"ctr": 0.7, "engagement": 0.6},
    "promoted_pin": {"ctr": 1.1, "engagement": 1.0},
    # Shopping/commerce - higher intent
    "shopping_carousel": {"ctr": 1.2, "engagement": 0.9},
    "shopping_ads": {"ctr": 1.3, "engagement": 0.8},
    "shopping_ad": {"ctr": 1.2, "engagement": 0.9},
    # Stories/ephemeral - high engagement
    "social_stories": {"ctr": 1.4, "engagement": 1.5},
    "story_ad": {"ctr": 1.3, "engagement": 1.4},
    "snap_ad": {"ctr": 1.2, "engagement": 1.3},
    # Search - high intent
    "search_text": {"ctr": 1.6, "engagement": 0.7},
    "discovery_ads": {"ctr": 1.1, "engagement": 0.9},
    # Branded/sponsored - awareness focused
    "sponsored_content": {"ctr": 0.9, "engagement": 1.1},
    "promoted_tweet": {"ctr": 0.8, "engagement": 1.0},
    "promoted_video": {"ctr": 1.1, "engagement": 1.2},
    "promoted_post": {"ctr": 0.85, "engagement": 1.0},
    "amplify_pre_roll": {"ctr": 0.95, "engagement": 1.1},
    # Premium placements
    "top_view": {"ctr": 1.5, "engagement": 1.6},
    "takeover": {"ctr": 1.4, "engagement": 1.5},
    "commercial": {"ctr": 1.1, "engagement": 1.2},
    # Other formats
    "spark_ads": {"ctr": 1.3, "engagement": 1.4},
    "branded_hashtag": {"ctr": 0.8, "engagement": 1.8},
    "carousel_ad": {"ctr": 1.15, "engagement": 1.1},
    "collection_ad": {"ctr": 1.2, "engagement": 1.0},
    "message_ads": {"ctr": 0.6, "engagement": 0.8},
    "text_ads": {"ctr": 0.75, "engagement": 0.6},
}


def truncated_normal(mean: float, std: float, min_val: float, max_val: float) -> float:
    """Generate a value from truncated normal distribution."""
    val = np.random.normal(mean, std)
    return float(np.clip(val, min_val, max_val))


def log_normal_value(mean: float, std: float, min_val: float, max_val: float) -> float:
    """Generate a value from log-normal distribution (right-skewed)."""
    # Convert mean/std to log-normal parameters
    variance = std ** 2
    mu = np.log(mean ** 2 / np.sqrt(variance + mean ** 2))
    sigma = np.sqrt(np.log(1 + variance / mean ** 2))
    val = np.random.lognormal(mu, sigma)
    return float(np.clip(val, min_val, max_val))

# ============================================================
# DLT RESOURCES (One per table)
# ============================================================


@dlt.resource(
    name="sessions",
    write_disposition="append",
    columns={
        "session_id": {"data_type": "text", "primary_key": True},
        "date": {"data_type": "date"},
    },
)
def sessions_resource(
    session_data: List[Dict[str, Any]], batch_size: int = 1000
) -> Iterator[List[Dict[str, Any]]]:
    """
    Sessions resource - yields data in 1K batches

    dlt will automatically write each yielded batch as a separate parquet file
    """
    total_rows = len(session_data)

    for i in range(0, total_rows, batch_size):
        batch = session_data[i : i + batch_size]
        print(f"  → Sessions batch {i//batch_size + 1}: {len(batch)} rows")
        yield batch


@dlt.resource(
    name="attribution_touchpoints",
    write_disposition="append",
    columns={
        "touchpoint_id": {"data_type": "text", "primary_key": True},
        "session_id": {"data_type": "text"},
        "date": {"data_type": "date"},
    },
)
def touchpoints_resource(
    touchpoint_data: List[Dict[str, Any]], batch_size: int = 1000
) -> Iterator[List[Dict[str, Any]]]:
    """Attribution touchpoints resource"""
    total_rows = len(touchpoint_data)

    for i in range(0, total_rows, batch_size):
        batch = touchpoint_data[i : i + batch_size]
        print(f"  → Touchpoints batch {i//batch_size + 1}: {len(batch)} rows")
        yield batch


@dlt.resource(
    name="conversions",
    write_disposition="append",
    columns={
        "conversion_id": {"data_type": "text", "primary_key": True},
        "session_id": {"data_type": "text"},
        "date": {"data_type": "date"},
    },
)
def conversions_resource(
    conversion_data: List[Dict[str, Any]], batch_size: int = 1000
) -> Iterator[List[Dict[str, Any]]]:
    """Conversions resource"""
    total_rows = len(conversion_data)

    for i in range(0, total_rows, batch_size):
        batch = conversion_data[i : i + batch_size]
        print(f"  → Conversions batch {i//batch_size + 1}: {len(batch)} rows")
        yield batch


@dlt.resource(
    name="campaigns_daily",
    write_disposition="append",
    columns={"campaign_id": {"data_type": "text"}, "date": {"data_type": "date"}},
)
def campaigns_resource(
    campaign_data: List[Dict[str, Any]], batch_size: int = 1000
) -> Iterator[List[Dict[str, Any]]]:
    """Campaigns daily metrics resource"""
    total_rows = len(campaign_data)

    for i in range(0, total_rows, batch_size):
        batch = campaign_data[i : i + batch_size]
        print(f"  → Campaigns batch {i//batch_size + 1}: {len(batch)} rows")
        yield batch


@dlt.resource(
    name="ad_creatives",
    write_disposition="append",
    columns={"creative_id": {"data_type": "text"}, "date": {"data_type": "date"}},
)
def creatives_resource(
    creative_data: List[Dict[str, Any]], batch_size: int = 1000
) -> Iterator[List[Dict[str, Any]]]:
    """Ad creatives metrics resource"""
    total_rows = len(creative_data)

    for i in range(0, total_rows, batch_size):
        batch = creative_data[i : i + batch_size]
        print(f"  → Creatives batch {i//batch_size + 1}: {len(batch)} rows")
        yield batch


@dlt.resource(
    name="metadata_snapshots",
    write_disposition="replace",  # Replace daily snapshot
    columns={
        "entity_id": {"data_type": "text", "primary_key": True},
        "date": {"data_type": "date"},
    },
)
def metadata_resource(
    metadata_data: List[Dict[str, Any]],
) -> Iterator[List[Dict[str, Any]]]:
    """Metadata snapshots resource (replaced daily, not batched)"""
    print(f"  → Metadata snapshot: {len(metadata_data)} rows")
    yield metadata_data


# ============================================================
# DLT SOURCE (Combines all resources)
# ============================================================


@dlt.source(name="synthetic_marketing_data")
def marketing_data_source(
    sessions_data: List[Dict],
    touchpoints_data: List[Dict],
    conversions_data: List[Dict],
    campaigns_data: List[Dict],
    creatives_data: List[Dict],
    metadata_data: List[Dict],
    batch_size: int = 1000,
):
    """
    DLT source that combines all marketing data resources

    Single source = single pipeline run = transactional consistency
    """
    return [
        sessions_resource(sessions_data, batch_size),
        touchpoints_resource(touchpoints_data, batch_size),
        conversions_resource(conversions_data, batch_size),
        campaigns_resource(campaigns_data, batch_size),
        creatives_resource(creatives_data, batch_size),
        metadata_resource(metadata_data),
    ]


# ============================================================
# DATA GENERATION LOGIC (Simplified - uses same logic as before)
# ============================================================

# We'll create a lightweight wrapper that generates data in dict format
# instead of DataFrames (dlt prefers dicts)


def generate_marketing_data(run_date: date) -> Dict[str, List[Dict]]:
    """
    Generate all marketing data tables

    Returns dict format expected by dlt resources
    """
    current_date = run_date
    # anchor timestamps at the run date (end of day for past dates) so backfills stay inside their day
    now = datetime.combine(run_date, time(23, 59)) if run_date < date.today() else datetime.now()
    year = current_date.year
    month = current_date.month
    day = current_date.day

    # Load config for generation rules
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    row_dist = config.get("data_generation_rules", {}).get("row_distribution", {})
    num_sessions = row_dist.get("sessions", 2200)
    num_touchpoints = row_dist.get("attribution_touchpoints", 2500)
    num_conversions = row_dist.get("conversions", 150)
    num_campaigns = row_dist.get("campaigns_daily", 20)
    num_creatives = row_dist.get("ad_creatives", 130)

    channels = config.get(
        "channels", ["meta", "google_ads", "linkedin", "tiktok", "twitter"]
    )
    creative_types = config.get("creative_types", {})

    # Generate campaigns first (needed for foreign keys)
    campaigns = []
    campaign_ids = []

    # Add day-of-week variance (weekends typically lower)
    day_of_week = current_date.weekday()
    is_weekend = day_of_week >= 5
    daily_variance = np.random.uniform(0.85, 1.15) * (0.8 if is_weekend else 1.0)

    for i in range(num_campaigns):
        channel = channels[i % len(channels)]
        campaign_id = f"camp_{channel}_{i+1:03d}"
        campaign_ids.append(campaign_id)

        # Get channel-specific profile
        profile = CHANNEL_PROFILES.get(channel, CHANNEL_PROFILES["meta"])

        # Generate channel-specific CTR using truncated normal
        ctr = truncated_normal(
            profile["ctr_mean"],
            profile["ctr_std"],
            profile["ctr_mean"] * 0.3,  # min ~30% of mean
            profile["ctr_mean"] * 2.5   # max ~250% of mean
        )

        # Generate channel-specific CPC using truncated normal
        cpc = truncated_normal(
            profile["cpc_mean"],
            profile["cpc_std"],
            profile["cpc_mean"] * 0.4,  # min ~40% of mean
            profile["cpc_mean"] * 2.0   # max ~200% of mean
        )

        # Budget with some variance between campaigns
        daily_budget = truncated_normal(2500, 800, 1000, 5000)

        # Spend ratio with higher variance (some overspend, some underspend)
        spend_ratio = truncated_normal(0.85, 0.15, 0.5, 1.15) * daily_variance
        spend = daily_budget * spend_ratio

        # Derive impressions from spend and CPM (which relates to CPC and CTR)
        estimated_cpm = (cpc / ctr) if ctr > 0 else 10.0
        impressions = int((spend / estimated_cpm) * 1000 * np.random.uniform(0.9, 1.1))

        # Derive clicks from impressions and CTR
        clicks = int(impressions * ctr * np.random.uniform(0.95, 1.05))

        campaigns.append(
            {
                "campaign_id": campaign_id,
                "campaign_name": f"{channel.title()} Campaign {i+1}",
                "channel": channel,
                "status": "active" if i < num_campaigns * 0.9 else "paused",
                "daily_budget": round(daily_budget, 2),
                "spend": round(spend, 2),
                "impressions": max(1000, impressions),
                "clicks": max(10, clicks),
                "ctr": round(ctr, 4),
                "cpc": round(cpc, 2),
                "date": str(current_date),
                "year": year,
                "month": month,
                "day": day,
            }
        )

    # Generate ad creatives (multiple per campaign)
    creatives = []
    creative_ids = []

    creatives_per_campaign = max(1, num_creatives // num_campaigns)
    creative_idx = 0

    for campaign in campaigns:
        channel = campaign["channel"]
        channel_creative_types = creative_types.get(channel, ["default"])

        # Generate 2-3 creatives per campaign
        num_creatives_for_campaign = min(
            creatives_per_campaign, len(channel_creative_types)
        )

        for j in range(num_creatives_for_campaign):
            if creative_idx >= num_creatives:
                break

            creative_type = channel_creative_types[j % len(channel_creative_types)]
            creative_id = (
                f'cre_{channel}_{campaign["campaign_id"].split("_")[-1]}_{j+1:02d}'
            )
            creative_ids.append(creative_id)

            # Get creative type multiplier
            type_mult = CREATIVE_TYPE_MULTIPLIERS.get(
                creative_type, {"ctr": 1.0, "engagement": 1.0}
            )

            # Base CTR from campaign, modified by creative type
            base_ctr = campaign["ctr"]
            creative_ctr = base_ctr * type_mult["ctr"] * np.random.uniform(0.85, 1.15)
            creative_ctr = max(0.001, min(0.15, creative_ctr))  # Bound to realistic range

            # Distribution of spend/impressions across creatives (not uniform)
            # Some creatives get more budget than others
            spend_share = log_normal_value(0.25, 0.1, 0.1, 0.5)
            creative_spend = campaign["spend"] * spend_share
            creative_impressions = int(campaign["impressions"] * spend_share * np.random.uniform(0.9, 1.1))
            creative_clicks = int(creative_impressions * creative_ctr)

            creatives.append(
                {
                    "creative_id": creative_id,
                    "campaign_id": campaign["campaign_id"],
                    "channel": channel,
                    "creative_type": creative_type,
                    "creative_name": f'{creative_type.replace("_", " ").title()} {j+1}',
                    "impressions": max(100, creative_impressions),
                    "clicks": max(1, creative_clicks),
                    "ctr": round(creative_ctr, 4),
                    "spend": round(creative_spend, 2),
                    "date": str(current_date),
                    "year": year,
                    "month": month,
                    "day": day,
                }
            )
            creative_idx += 1

    # Generate sessions
    sessions = []
    session_ids = []

    # Build a lookup for campaign channel conversion rates
    campaign_conv_rates = {}
    for campaign in campaigns:
        channel = campaign["channel"]
        profile = CHANNEL_PROFILES.get(channel, CHANNEL_PROFILES["meta"])
        campaign_conv_rates[campaign["campaign_id"]] = profile["conv_rate"]

    for i in range(num_sessions):
        campaign_id = campaign_ids[i % len(campaign_ids)]
        # Get matching creative for this campaign
        matching_creatives = [
            c["creative_id"] for c in creatives if c["campaign_id"] == campaign_id
        ]
        creative_id = (
            matching_creatives[i % len(matching_creatives)]
            if matching_creatives
            else creative_ids[i % len(creative_ids)]
        )

        session_id = f'sess_{current_date.strftime("%Y%m%d")}_{i:06d}'
        session_ids.append(session_id)

        channel = campaign_id.split("_")[1]

        # Generate device and country first (they affect other metrics)
        device_type = np.random.choice(
            ["mobile", "desktop", "tablet"], p=[0.68, 0.25, 0.07]
        )
        country = np.random.choice(
            ["us", "uk", "de", "es", "fr"], p=[0.45, 0.15, 0.12, 0.10, 0.18]
        )

        # Get modifiers
        device_mod = DEVICE_MODIFIERS.get(device_type, DEVICE_MODIFIERS["mobile"])
        country_mod = COUNTRY_MODIFIERS.get(country, COUNTRY_MODIFIERS["us"])

        # Session duration: log-normal (right-skewed), mean ~125s, modified by device
        base_duration = log_normal_value(125, 45, 10, 600)
        session_duration = int(base_duration * device_mod["session_duration"])
        session_duration = max(10, min(600, session_duration))

        # Pages viewed: log-normal (right-skewed), mean ~3.2, modified by device
        # Correlate somewhat with session duration
        duration_factor = (session_duration / 125) ** 0.3  # Weak correlation
        base_pages = log_normal_value(3.2, 1.8, 1, 15)
        pages_viewed = int(base_pages * device_mod["pages"] * duration_factor)
        pages_viewed = max(1, min(15, pages_viewed))

        sessions.append(
            {
                "session_id": session_id,
                "user_id": f"user_{i%50000:06d}",
                "campaign_id": campaign_id,
                "creative_id": creative_id,
                "channel": channel,
                "session_start": (
                    now - timedelta(hours=i % 24, minutes=i % 60)
                ).isoformat(),
                "session_duration_sec": session_duration,
                "pages_viewed": pages_viewed,
                "device_type": device_type,
                "country": country,
                "date": str(current_date),
                "year": year,
                "month": month,
                "day": day,
                # Store modifiers for conversion probability calculation
                "_conv_prob": (
                    campaign_conv_rates.get(campaign_id, 0.05)
                    * device_mod["conv_rate"]
                    * country_mod["conv_rate"]
                ),
            }
        )

    # Generate conversions using weighted selection based on conversion probability
    conversions = []
    conversion_session_ids = []

    # Calculate conversion probabilities for all sessions
    conv_probs = np.array([s.get("_conv_prob", 0.05) for s in sessions])
    conv_probs = conv_probs / conv_probs.sum()  # Normalize to probabilities

    # Select sessions that will convert (weighted by their conversion probability)
    converting_indices = np.random.choice(
        len(sessions),
        size=min(num_conversions, len(sessions)),
        replace=False,
        p=conv_probs
    )

    for i, session_idx in enumerate(converting_indices):
        session = sessions[session_idx]
        session_id = session["session_id"]
        conversion_session_ids.append(session_id)

        # Conversion value: log-normal (many small purchases, few large)
        # Mean ~180, with long tail up to 800
        conversion_value = log_normal_value(180, 60, 20, 800)

        conversions.append(
            {
                "conversion_id": f'conv_{current_date.strftime("%Y%m%d")}_{i:05d}',
                "session_id": session_id,
                "user_id": session["user_id"],
                "attributed_campaign_id": session["campaign_id"],
                "attribution_model": "first_touch",
                "conversion_value": round(conversion_value, 2),
                "timestamp": (now - timedelta(hours=i % 24)).isoformat(),
                "date": str(current_date),
                "year": year,
                "month": month,
                "day": day,
            }
        )

    # Clean up internal fields from sessions before returning
    for session in sessions:
        session.pop("_conv_prob", None)

    # Generate attribution touchpoints (multi-touch journeys)
    touchpoints = []
    touchpoint_idx = 0

    # Create touchpoints for converting sessions (2-5 touchpoints each)
    for session_id in conversion_session_ids:
        session = next(s for s in sessions if s["session_id"] == session_id)
        num_touchpoints_for_user = int(np.random.uniform(2, 5))

        for t in range(num_touchpoints_for_user):
            if touchpoint_idx >= num_touchpoints:
                break

            # First touchpoint is always the converting session's campaign
            # Others are random campaigns
            if t == 0:
                touchpoint_campaign_id = session["campaign_id"]
            else:
                touchpoint_campaign_id = campaign_ids[
                    touchpoint_idx % len(campaign_ids)
                ]

            touchpoint_channel = touchpoint_campaign_id.split("_")[1]

            touchpoints.append(
                {
                    "touchpoint_id": f'tp_{current_date.strftime("%Y%m%d")}_{touchpoint_idx:06d}',
                    "session_id": session_id,
                    "user_id": session["user_id"],
                    "campaign_id": touchpoint_campaign_id,
                    "channel": touchpoint_channel,
                    "touchpoint_position": t + 1,
                    "timestamp": (
                        now - timedelta(days=t, hours=touchpoint_idx % 24)
                    ).isoformat(),
                    "date": str(current_date),
                    "year": year,
                    "month": month,
                    "day": day,
                }
            )
            touchpoint_idx += 1

    # Fill remaining touchpoints quota with non-converting sessions
    remaining_touchpoints = num_touchpoints - len(touchpoints)
    if remaining_touchpoints > 0:
        # Add touchpoints for non-converting sessions
        non_converting_sessions = [
            s for s in sessions if s["session_id"] not in conversion_session_ids
        ]

        for i in range(min(remaining_touchpoints, len(non_converting_sessions))):
            session = non_converting_sessions[i % len(non_converting_sessions)]

            touchpoints.append(
                {
                    "touchpoint_id": f'tp_{current_date.strftime("%Y%m%d")}_{touchpoint_idx:06d}',
                    "session_id": session["session_id"],
                    "user_id": session["user_id"],
                    "campaign_id": session["campaign_id"],
                    "channel": session["channel"],
                    "touchpoint_position": 1,
                    "timestamp": session["session_start"],
                    "date": str(current_date),
                    "year": year,
                    "month": month,
                    "day": day,
                }
            )
            touchpoint_idx += 1

    # Generate metadata snapshots
    metadata = []

    # Campaign metadata
    for campaign in campaigns:
        metadata.append(
            {
                "entity_id": campaign["campaign_id"],
                "entity_type": "campaign",
                "name": campaign["campaign_name"],
                "channel": campaign["channel"],
                "status": campaign["status"],
                "created_at": (now - timedelta(days=30)).isoformat(),
                "updated_at": now.isoformat(),
                "date": str(current_date),
                "year": year,
                "month": month,
                "day": day,
            }
        )

    # Creative metadata
    for creative in creatives:
        metadata.append(
            {
                "entity_id": creative["creative_id"],
                "entity_type": "creative",
                "name": creative["creative_name"],
                "channel": creative["channel"],
                "creative_type": creative["creative_type"],
                "campaign_id": creative["campaign_id"],
                "created_at": (now - timedelta(days=15)).isoformat(),
                "updated_at": now.isoformat(),
                "date": str(current_date),
                "year": year,
                "month": month,
                "day": day,
            }
        )

    return {
        "sessions": sessions,
        "touchpoints": touchpoints,
        "conversions": conversions,
        "campaigns": campaigns,
        "creatives": creatives,
        "metadata": metadata,
    }


# ============================================================
# MAIN PIPELINE FUNCTION
# ============================================================


def run_dlt_pipeline(run_date: date, batch_size: int = 1000):
    """
    Main entry point - runs the complete dlt pipeline

    Args:
        batch_size: Rows per parquet file (default 1000)
    """

    print("\n" + "=" * 60)
    print("DLT Marketing Data Pipeline")
    if LOCAL_MODE:
        print(f"Mode: LOCAL (writing to ./data/output)")
    else:
        print(f"Mode: S3 (writing to s3://{S3_BUCKET}/{S3_PREFIX})")
    print("=" * 60 + "\n")

    # Step 1: Generate data
    print("1. Generating marketing data...")
    data = generate_marketing_data(run_date)

    for table, rows in data.items():
        print(f"   {table}: {len(rows)} rows")

    print()

    # Step 2: Configure pipeline
    print("2. Configuring dlt pipeline...")

    if LOCAL_MODE:
        # Use local filesystem destination with date-based partitioning
        # dataset_name becomes the top-level directory (matching S3 structure)
        pipeline = dlt.pipeline(
            pipeline_name="marketing_data_pipeline",
            destination=filesystem(
                bucket_url=str(LOCAL_OUTPUT_DIR),
                layout="{table_name}/year={YYYY}/month={MM}/day={DD}/{table_name}_batch_{file_id}.parquet",
                current_datetime=pendulum.datetime(run_date.year, run_date.month, run_date.day),
            ),
            dataset_name=S3_PREFIX,  # Use same prefix as S3 for consistency
        )
        print(f"   Pipeline: {pipeline.pipeline_name}")
        print(f"   Destination: {LOCAL_OUTPUT_DIR}")
        print(f"   Batch size: {batch_size} rows/file\n")
    else:
        # Use S3 destination with date-based partitioning
        # dataset_name becomes the top-level prefix
        pipeline = dlt.pipeline(
            pipeline_name="marketing_data_pipeline",
            destination=filesystem(
                bucket_url=f"s3://{S3_BUCKET}",
                credentials={
                    "aws_access_key_id": _linked("ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID"),
                    "aws_secret_access_key": _linked("SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY"),
                    "region_name": _linked("REGION") or os.getenv("S3_REGION") or os.getenv("AWS_REGION", "us-east-1"),
                },
                layout="{table_name}/year={YYYY}/month={MM}/day={DD}/{table_name}_batch_{file_id}.parquet",
                current_datetime=pendulum.datetime(run_date.year, run_date.month, run_date.day),
            ),
            dataset_name=S3_PREFIX,  # Use S3_PREFIX as dataset_name
        )
        print(f"   Pipeline: {pipeline.pipeline_name}")
        print(f"   Destination: s3://{S3_BUCKET}/{S3_PREFIX}")
        print(f"   Linked S3 variables: {sorted(k for k in os.environ if k.startswith('AWS_S3__'))}")
        print(f"   Batch size: {batch_size} rows/file\n")

    # Step 3: Create source with all resources
    print("3. Loading data with dlt...\n")

    source = marketing_data_source(
        sessions_data=data["sessions"],
        touchpoints_data=data["touchpoints"],
        conversions_data=data["conversions"],
        campaigns_data=data["campaigns"],
        creatives_data=data["creatives"],
        metadata_data=data["metadata"],
        batch_size=batch_size,
    )

    # Step 4: Run pipeline
    load_info = pipeline.run(source, loader_file_format="parquet")

    # Step 5: Display results
    print("\n4. Pipeline Results:")
    print(f"   Status: {'✓ SUCCESS' if load_info else '✗ FAILED'}")

    if load_info:
        print(f"   Load ID: {load_info.loads_ids[0] if load_info.loads_ids else 'N/A'}")
        print(f"   Packages: {len(load_info.load_packages)}")

        for package in load_info.load_packages:
            print(f"\n   Package: {package.load_id}")
            if hasattr(package, "jobs") and package.jobs:
                for job in package.jobs:
                    if hasattr(job, "state"):
                        if job.state == "completed":
                            print(f"     ✓ {job.job_file_info.table_name}")
                    else:
                        print(f"     • {job}")

    print("\n" + "=" * 60)
    print("✓ Pipeline Complete!")
    print("=" * 60 + "\n")

    return load_info


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate marketing data into S3")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Rows per parquet file (default: 1000)",
    )
    parser.add_argument("--from-date", type=date.fromisoformat, help="First day to generate, YYYY-MM-DD (default: today)")
    parser.add_argument("--to-date", type=date.fromisoformat, help="Last day to generate, inclusive (default: --from-date)")
    args = parser.parse_args()

    start = args.from_date or date.today()
    end = args.to_date or start
    for offset in range((end - start).days + 1):
        day = start + timedelta(days=offset)
        run_dlt_pipeline(day, batch_size=args.batch_size)
