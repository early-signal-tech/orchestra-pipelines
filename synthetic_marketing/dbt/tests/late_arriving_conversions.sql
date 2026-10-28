-- Conversion events that landed more than two days after they happened.
{{ config(tags=['data_quality']) }}
select conversion_id, date, "timestamp"
from {{ source('marketing_raw', 'conversions') }}
where cast("timestamp" as timestamp) < cast(date as date) - interval 2 day
