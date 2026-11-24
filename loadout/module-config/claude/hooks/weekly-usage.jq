def workday: ((. - (5 * 3600)) | strflocaltime("%Y-%m-%d") | . + "T00:00:00Z" | fromdateiso8601);
def today_left($now): if . == null or .used_percentage == null or .resets_at == null then ""
  else (((((($now | workday) - ((.resets_at - 604800) | workday)) / 86400) | floor) + 1)
        | if . < 1 then 1 elif . > 7 then 7 else . end) as $day
    | (($day * 100 / 7) - .used_percentage | round) end;
