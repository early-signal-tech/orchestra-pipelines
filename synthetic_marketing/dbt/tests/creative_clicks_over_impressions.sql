-- More clicks than impressions: the tracker double counted.
{{ config(tags=['data_quality']) }}
select creative_id, date, clicks, impressions
from {{ source('marketing_raw', 'ad_creatives') }}
where clicks > impressions
