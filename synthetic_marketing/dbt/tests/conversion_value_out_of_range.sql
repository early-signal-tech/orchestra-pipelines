-- Negative values (refund sign flipped) or values far above any order (sent in cents).
{{ config(severity='warn') }}
select conversion_id, date, conversion_value
from {{ source('marketing_raw', 'conversions') }}
where conversion_value <= 0 or conversion_value > 5000
