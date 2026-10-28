-- Campaigns that spent more than 1.2x their daily budget (pacing broke).
{{ config(severity='warn') }}
select campaign_id, date, spend, daily_budget
from {{ source('marketing_raw', 'campaigns_daily') }}
where spend > daily_budget * 1.2
