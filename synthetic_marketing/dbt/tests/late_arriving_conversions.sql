-- Conversion events that landed more than two days after they happened.
{{ config(severity='warn') }}
select conversion_id, date, "timestamp"
from {{ source('marketing_raw', 'conversions') }}
where cast("timestamp" as timestamp) < cast(date as date) - interval 2 day
