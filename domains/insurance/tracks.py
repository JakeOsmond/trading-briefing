"""Insurance investigation tracks — 23 deterministic SQL queries for trading analysis."""


def build_investigation_tracks(dp, policies_table, web_table):
    """Build all investigation track SQL queries. Each compares TY vs LY in one query."""
    P = policies_table
    W = web_table
    tracks = {}

    # Track 1: Channel × Product Matrix — the core GP decomposition
    tracks['channel_product_mix'] = {
        'name': 'Channel × Product Matrix',
        'desc': 'GP decomposition by distribution channel and policy type',
        'sql': f"""
SELECT 'TY' AS yr, distribution_channel, policy_type,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
    SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_discount
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY distribution_channel, policy_type
UNION ALL
SELECT 'LY', distribution_channel, policy_type,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY distribution_channel, policy_type
"""
    }

    # Track 2: Scheme performance — top schemes ranked by GP
    tracks['scheme_performance'] = {
        'name': 'Scheme Performance',
        'desc': 'Individual scheme GP, volume, and pricing',
        'sql': f"""
SELECT 'TY' AS yr, scheme_name,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY scheme_name
HAVING ABS(SUM(policy_count)) >= 5
UNION ALL
SELECT 'LY', scheme_name,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY scheme_name
HAVING ABS(SUM(policy_count)) >= 5
ORDER BY gp DESC
"""
    }

    # Track 3: Medical vs Non-Medical
    tracks['medical_profile'] = {
        'name': 'Medical vs Non-Medical',
        'desc': 'Risk segment decomposition — medical screening impact on margin',
        'sql': f"""
SELECT 'TY' AS yr,
    CASE WHEN max_medical_score > 0 THEN 'Medical' ELSE 'Non-medical' END AS medical_flag,
    max_medical_score_grouped, policy_type, distribution_channel,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_premium,
    SUM(CAST(medical_net_to_underwriter AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_uw_cost
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY medical_flag, max_medical_score_grouped, policy_type, distribution_channel
UNION ALL
SELECT 'LY' AS yr,
    CASE WHEN max_medical_score > 0 THEN 'Medical' ELSE 'Non-medical' END AS medical_flag,
    max_medical_score_grouped, policy_type, distribution_channel,
    SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_premium,
    SUM(CAST(medical_net_to_underwriter AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_uw_cost
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY medical_flag, max_medical_score_grouped, policy_type, distribution_channel
"""
    }

    # Track 4: Cover Level Mix
    tracks['cover_level_mix'] = {
        'name': 'Cover Level & Upsell Mix',
        'desc': 'Customer tier choices and add-on attach rates',
        'sql': f"""
SELECT 'TY' AS yr, cover_level_name, cover_level_tier,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(base_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_base_price,
    SUM(CAST(option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_option_price,
    SUM(CAST(total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gadget_price,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY cover_level_name, cover_level_tier
UNION ALL
SELECT 'LY', cover_level_name, cover_level_tier,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(base_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY cover_level_name, cover_level_tier
"""
    }

    # Track 5: Commission & Partner Economics
    tracks['commission_partners'] = {
        'name': 'Commission & Partner Economics',
        'desc': 'Cost structure by agent, partner, and distribution channel',
        'sql': f"""
SELECT 'TY' AS yr, insurance_group, distribution_channel,
    SUM(policy_count) AS policies,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) AS total_commission,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(NULLIF(SUM(CAST(total_gross_inc_ipt AS FLOAT64)), 0), 0) AS commission_rate,
    SUM(CAST(campaign_commission_value AS FLOAT64)) AS campaign_commission,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY insurance_group, distribution_channel
HAVING ABS(SUM(policy_count)) >= 3
UNION ALL
SELECT 'LY', insurance_group, distribution_channel,
    SUM(policy_count), SUM(CAST(total_paid_commission_value AS FLOAT64)),
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(NULLIF(SUM(CAST(total_gross_inc_ipt AS FLOAT64)), 0), 0),
    SUM(CAST(campaign_commission_value AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY insurance_group, distribution_channel
HAVING ABS(SUM(policy_count)) >= 3
"""
    }

    # Track 6: Customer Demographics (Age & Type)
    tracks['customer_demographics'] = {
        'name': 'Customer Demographics',
        'desc': 'Age profile and new vs existing customer dynamics',
        'sql': f"""
SELECT 'TY' AS yr, customer_type, customer_type_insurance_only,
    CASE
        WHEN max_age_at_purchase < 35 THEN 'Under 35'
        WHEN max_age_at_purchase BETWEEN 35 AND 54 THEN '35-54'
        WHEN max_age_at_purchase BETWEEN 55 AND 69 THEN '55-69'
        WHEN max_age_at_purchase BETWEEN 70 AND 79 THEN '70-79'
        WHEN max_age_at_purchase >= 80 THEN '80+'
    END AS age_band,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY customer_type, customer_type_insurance_only, age_band
UNION ALL
SELECT 'LY' AS yr, customer_type, customer_type_insurance_only,
    CASE
        WHEN max_age_at_purchase < 35 THEN 'Under 35'
        WHEN max_age_at_purchase BETWEEN 35 AND 54 THEN '35-54'
        WHEN max_age_at_purchase BETWEEN 55 AND 69 THEN '55-69'
        WHEN max_age_at_purchase BETWEEN 70 AND 79 THEN '70-79'
        WHEN max_age_at_purchase >= 80 THEN '80+'
    END AS age_band,
    SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY customer_type, customer_type_insurance_only, age_band
"""
    }

    # Track 7: Destination Mix
    tracks['destination_mix'] = {
        'name': 'Destination & Region Mix',
        'desc': 'Geographic patterns — destination groups and customer regions',
        'sql': f"""
SELECT 'TY' AS yr, destination_group,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY destination_group
UNION ALL
SELECT 'LY', destination_group,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY destination_group
"""
    }

    # Track 8: Cancellation Analysis
    tracks['cancellations'] = {
        'name': 'Cancellation Analysis',
        'desc': 'Cancellation patterns by reason, channel, and policy type',
        'sql': f"""
SELECT 'TY' AS yr, cancellation_reason, policy_type, distribution_channel,
    SUM(policy_count) AS cancellations,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp_impact
FROM {P}
WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  AND transaction_type = 'Cancellation'
GROUP BY cancellation_reason, policy_type, distribution_channel
UNION ALL
SELECT 'LY', cancellation_reason, policy_type, distribution_channel,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
FROM {P}
WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  AND transaction_type = 'Cancellation'
GROUP BY cancellation_reason, policy_type, distribution_channel
"""
    }

    # Track 9: Renewal Performance
    tracks['renewals'] = {
        'name': 'Renewal Performance',
        'desc': 'Renewal rate (expiry→renewal), expiry mix by channel, cohort analysis',
        'sql': f"""
-- Part A: Blended renewal rate — expiring policies vs renewed policies (weekly)
WITH expiry_pols AS (
    SELECT 'TY' AS yr, SUM(policy_count) AS expiring,
        SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS expiring_gp
    FROM {P}
    WHERE travel_end_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND LOWER(policy_type) = 'annual'
    UNION ALL
    SELECT 'LY', SUM(policy_count),
        SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
    FROM {P}
    WHERE travel_end_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND LOWER(policy_type) = 'annual'
),
renewal_pols AS (
    SELECT 'TY' AS yr, SUM(policy_count) AS renewed,
        SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS renewed_gp
    FROM {P}
    WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND LOWER(distribution_channel) = 'renewals'
    UNION ALL
    SELECT 'LY', SUM(policy_count),
        SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64))
    FROM {P}
    WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND LOWER(distribution_channel) = 'renewals'
)
SELECT e.yr, e.expiring, e.expiring_gp,
    SAFE_DIVIDE(e.expiring_gp, e.expiring) AS avg_expiry_gp,
    r.renewed, r.renewed_gp,
    SAFE_DIVIDE(r.renewed_gp, r.renewed) AS avg_renewed_gp,
    SAFE_DIVIDE(r.renewed, e.expiring) AS renewal_rate
FROM expiry_pols e LEFT JOIN renewal_pols r ON e.yr = r.yr
ORDER BY e.yr
""",
        'sql_2': f"""
-- Part B: Expiry mix by original distribution channel (explains blended rate shifts)
SELECT 'TY' AS yr, distribution_channel AS expiry_channel,
    SUM(policy_count) AS expiring_policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS expiring_gp,
    SAFE_DIVIDE(SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), NULLIF(SUM(policy_count),0)) AS avg_gp
FROM {P}
WHERE travel_end_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  AND LOWER(policy_type) = 'annual'
GROUP BY distribution_channel
UNION ALL
SELECT 'LY', distribution_channel,
    SUM(policy_count),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SAFE_DIVIDE(SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), NULLIF(SUM(policy_count),0))
FROM {P}
WHERE travel_end_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  AND LOWER(policy_type) = 'annual'
GROUP BY distribution_channel
ORDER BY yr, expiring_policies DESC
""",
        'sql_3': f"""
-- Part C: Renewal cohort detail — retention, pricing, auto-renew
SELECT 'TY' AS yr, policy_renewal_year, auto_renew_opt_in,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price
FROM {P}
WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  AND distribution_channel = 'Renewals'
GROUP BY policy_renewal_year, auto_renew_opt_in
UNION ALL
SELECT 'LY', policy_renewal_year, auto_renew_opt_in,
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P}
WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  AND distribution_channel = 'Renewals'
GROUP BY policy_renewal_year, auto_renew_opt_in
"""
    }

    # Track 10: Web Funnel — detailed page-level, device-specific conversion
    tracks['web_funnel_detailed'] = {
        'name': 'Web Funnel (Detailed)',
        'desc': 'Page-level conversion by device — where users drop off',
        'sql': f"""
SELECT 'TY' AS yr, device_type, page_type,
    COUNT(DISTINCT session_id) AS page_sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'click' AND event_name IN
        ('engine_search_button','continue-button','continue_button','select_product',
         'book-button','go-to-checkout','verisk-continue')
        THEN session_id END) AS action_sessions
FROM {W}
WHERE session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  AND page_type IN ('landing','gatekeeper/description/1','extra_details',
    'screening','search_results','addon_results','checkout_new_user',
    'checkout_authenticated','just_booked')
  AND device_type IN ('mobile','computer','tablet')
GROUP BY device_type, page_type
UNION ALL
SELECT 'LY', device_type, page_type,
    COUNT(DISTINCT session_id),
    COUNT(DISTINCT CASE WHEN event_type = 'click' AND event_name IN
        ('engine_search_button','continue-button','continue_button','select_product',
         'book-button','go-to-checkout','verisk-continue')
        THEN session_id END)
FROM {W}
WHERE session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  AND page_type IN ('landing','gatekeeper/description/1','extra_details',
    'screening','search_results','addon_results','checkout_new_user',
    'checkout_authenticated','just_booked')
  AND device_type IN ('mobile','computer','tablet')
GROUP BY device_type, page_type
"""
    }

    # Track 11: Day-of-Week Patterns
    tracks['day_of_week'] = {
        'name': 'Day-of-Week Patterns',
        'desc': 'Daily GP pattern within the trailing week — spot individual bad days',
        'sql': f"""
SELECT 'TY' AS yr, transaction_date,
    FORMAT_DATE('%A', transaction_date) AS day_name,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY transaction_date
UNION ALL
SELECT 'LY', transaction_date,
    FORMAT_DATE('%A', transaction_date),
    SUM(policy_count), SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY transaction_date
ORDER BY transaction_date
"""
    }

    # Track 12: Discount & Campaign Effectiveness
    tracks['discounts_campaigns'] = {
        'name': 'Discount & Campaign Effectiveness',
        'desc': 'Discount penetration and campaign ROI',
        'sql': f"""
SELECT 'TY' AS yr,
    CASE WHEN CAST(total_discount_value AS FLOAT64) != 0 THEN 'Discounted' ELSE 'Full price' END AS discount_flag,
    campaign_name,
    SUM(policy_count) AS policies,
    SUM(CAST(total_discount_value AS FLOAT64)) AS total_discounts,
    SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_discount,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY discount_flag, campaign_name
HAVING ABS(SUM(policy_count)) >= 2
UNION ALL
SELECT 'LY' AS yr,
    CASE WHEN CAST(total_discount_value AS FLOAT64) != 0 THEN 'Discounted' ELSE 'Full price' END AS discount_flag,
    campaign_name,
    SUM(policy_count) AS policies, SUM(CAST(total_discount_value AS FLOAT64)) AS total_discounts,
    SUM(CAST(total_discount_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_discount,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY discount_flag, campaign_name
HAVING ABS(SUM(policy_count)) >= 2
"""
    }

    # Track 13: Cruise vs Non-Cruise
    tracks['cruise'] = {
        'name': 'Cruise vs Non-Cruise',
        'desc': 'Cruise segment performance — partner and scheme analysis',
        'sql': f"""
SELECT 'TY' AS yr,
    CASE WHEN LOWER(scheme_name) LIKE '%cruise%' OR LOWER(campaign_name) LIKE '%cru%' THEN 'Cruise' ELSE 'Non-Cruise' END AS cruise_flag,
    distribution_channel, agent_name,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY cruise_flag, distribution_channel, agent_name
HAVING ABS(SUM(policy_count)) >= 2
UNION ALL
SELECT 'LY' AS yr,
    CASE WHEN LOWER(scheme_name) LIKE '%cruise%' OR LOWER(campaign_name) LIKE '%cru%' THEN 'Cruise' ELSE 'Non-Cruise' END AS cruise_flag,
    distribution_channel, agent_name,
    SUM(policy_count) AS policies, SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY cruise_flag, distribution_channel, agent_name
HAVING ABS(SUM(policy_count)) >= 2
"""
    }

    # -----------------------------------------------------------------------
    # CROSS-TABLE TRACKS — joining web behaviour to trading outcomes
    # -----------------------------------------------------------------------

    # Track 14: Session-to-GP Bridge — device × scheme × medical screening
    tracks['web_to_gp_bridge'] = {
        'name': 'Session-to-GP Bridge (Device × Scheme × Medical)',
        'desc': 'Which web journeys (device, scheme, medical screening) produce the highest and lowest GP per converting session? Joins every converting web session to its policy outcome to show where high-value customers actually come from.',
        'sql': f"""
WITH converting_sessions_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        w.scheme_name AS web_scheme,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.certificate_id IS NOT NULL
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type, w.scheme_name
),
joined_ty AS (
    SELECT
        'TY' AS yr,
        cs.device_type,
        cs.web_scheme,
        CASE WHEN cs.had_medical = 1 THEN 'Medical' ELSE 'Non-medical' END AS medical_flag,
        SUM(p.policy_count) AS policies,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
        SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) AS total_gross,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy,
        COUNT(DISTINCT cs.session_id) AS converting_sessions,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(COUNT(DISTINCT cs.session_id), 0) AS gp_per_session
    FROM converting_sessions_ty cs
    JOIN {P} p ON CAST(p.certificate_id AS STRING) = cs.certificate_id
    WHERE p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
    GROUP BY cs.device_type, cs.web_scheme, medical_flag
    HAVING ABS(SUM(p.policy_count)) >= 3
),
converting_sessions_ly AS (
    SELECT
        w.session_id,
        w.device_type,
        w.scheme_name AS web_scheme,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.certificate_id IS NOT NULL
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type, w.scheme_name
),
joined_ly AS (
    SELECT
        'LY' AS yr,
        cs.device_type,
        cs.web_scheme,
        CASE WHEN cs.had_medical = 1 THEN 'Medical' ELSE 'Non-medical' END AS medical_flag,
        SUM(p.policy_count) AS policies,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
        SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) AS total_gross,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy,
        COUNT(DISTINCT cs.session_id) AS converting_sessions,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(COUNT(DISTINCT cs.session_id), 0) AS gp_per_session
    FROM converting_sessions_ly cs
    JOIN {P} p ON CAST(p.certificate_id AS STRING) = cs.certificate_id
    WHERE p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
    GROUP BY cs.device_type, cs.web_scheme, medical_flag
    HAVING ABS(SUM(p.policy_count)) >= 3
)
SELECT * FROM joined_ty
UNION ALL
SELECT * FROM joined_ly
ORDER BY total_gp DESC
"""
    }

    # Track 15: Funnel Drop-off by GP Value Tier
    tracks['funnel_value_dropoff'] = {
        'name': 'Funnel Drop-off by Value Tier',
        'desc': 'Compares the web funnel for sessions that converted into high-GP vs low-GP policies vs sessions that never converted. Shows where high-value customers drop off vs low-value ones, revealing if the funnel is optimised for the wrong customer.',
        'sql': f"""
WITH policy_values_ty AS (
    SELECT certificate_id,
        SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS policy_gp,
        MAX(policy_type) AS policy_type
    FROM {P}
    WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND certificate_id IS NOT NULL
    GROUP BY certificate_id
),
session_values_ty AS (
    SELECT w.session_id, w.device_type,
        MAX(w.certificate_id) AS certificate_id,
        MAX(pv.policy_gp) AS policy_gp,
        MAX(pv.policy_type) AS policy_type,
        CASE
            WHEN MAX(pv.policy_gp) IS NULL THEN 'Non-converter'
            WHEN MAX(pv.policy_gp) >= 50 THEN 'High GP (50+)'
            WHEN MAX(pv.policy_gp) >= 20 THEN 'Mid GP (20-50)'
            ELSE 'Low GP (<20)'
        END AS value_tier
    FROM {W} w
    LEFT JOIN policy_values_ty pv ON CAST(pv.certificate_id AS STRING) = w.certificate_id
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
)
SELECT 'TY' AS yr, sv.value_tier, sv.device_type,
    COUNT(DISTINCT sv.session_id) AS sessions,
    COUNT(DISTINCT CASE WHEN w2.booking_flow_stage = 'Search' THEN sv.session_id END) AS reached_search,
    COUNT(DISTINCT CASE WHEN w2.page_type = 'search_results' THEN sv.session_id END) AS reached_results,
    COUNT(DISTINCT CASE WHEN w2.page_type = 'screening' THEN sv.session_id END) AS reached_screening,
    COUNT(DISTINCT CASE WHEN w2.booking_flow_stage = 'Checkout' THEN sv.session_id END) AS reached_checkout,
    COUNT(DISTINCT CASE WHEN w2.page_type = 'just_booked' THEN sv.session_id END) AS reached_booked
FROM session_values_ty sv
JOIN {W} w2 ON w2.session_id = sv.session_id
    AND w2.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY sv.value_tier, sv.device_type

UNION ALL

SELECT 'LY' AS yr, sv.value_tier, sv.device_type,
    COUNT(DISTINCT sv.session_id),
    COUNT(DISTINCT CASE WHEN w2.booking_flow_stage = 'Search' THEN sv.session_id END),
    COUNT(DISTINCT CASE WHEN w2.page_type = 'search_results' THEN sv.session_id END),
    COUNT(DISTINCT CASE WHEN w2.page_type = 'screening' THEN sv.session_id END),
    COUNT(DISTINCT CASE WHEN w2.booking_flow_stage = 'Checkout' THEN sv.session_id END),
    COUNT(DISTINCT CASE WHEN w2.page_type = 'just_booked' THEN sv.session_id END)
FROM (
    SELECT w.session_id, w.device_type,
        MAX(w.certificate_id) AS certificate_id,
        CASE
            WHEN MAX(pv.policy_gp) IS NULL THEN 'Non-converter'
            WHEN MAX(pv.policy_gp) >= 50 THEN 'High GP (50+)'
            WHEN MAX(pv.policy_gp) >= 20 THEN 'Mid GP (20-50)'
            ELSE 'Low GP (<20)'
        END AS value_tier
    FROM {W} w
    LEFT JOIN (
        SELECT certificate_id,
            SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS policy_gp
        FROM {P}
        WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
          AND certificate_id IS NOT NULL
        GROUP BY certificate_id
    ) pv ON CAST(pv.certificate_id AS STRING) = w.certificate_id
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) sv
JOIN {W} w2 ON w2.session_id = sv.session_id
    AND w2.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY sv.value_tier, sv.device_type
"""
    }

    # Track 16: Annual vs Single Conversion Path — YoY shift
    tracks['annual_vs_single_conversion'] = {
        'name': 'Annual vs Single Conversion Path (YoY)',
        'desc': 'How does the web-to-purchase path differ for annual vs single trip policies? Compares conversion rates, multi-search behaviour, medical screening involvement, and GP yield for each policy type. Shows if annual customers are being lost somewhere specific in the funnel.',
        'sql': f"""
WITH sessions_with_outcome_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(CASE WHEN w.Multiple_search = 'Yes' THEN 1 ELSE 0 END) AS had_multi_search,
        MAX(CASE WHEN w.booking_flow_stage = 'Search' THEN 1 ELSE 0 END) AS reached_search,
        MAX(CASE WHEN w.booking_flow_stage = 'Checkout' THEN 1 ELSE 0 END) AS reached_checkout,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS booked,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
),
with_policy_ty AS (
    SELECT s.*,
        p.policy_type,
        SUM(p.policy_count) AS policies,
        SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp
    FROM sessions_with_outcome_ty s
    LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = s.certificate_id
        AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
    GROUP BY s.session_id, s.device_type, s.had_medical, s.had_multi_search,
             s.reached_search, s.reached_checkout, s.booked, s.certificate_id, p.policy_type
)
SELECT 'TY' AS yr,
    COALESCE(policy_type, 'No conversion') AS policy_type,
    device_type,
    COUNT(DISTINCT session_id) AS total_sessions,
    SUM(reached_search) AS search_sessions,
    SUM(reached_checkout) AS checkout_sessions,
    SUM(booked) AS booked_sessions,
    SUM(had_medical) AS medical_sessions,
    SUM(had_multi_search) AS multi_search_sessions,
    SUM(gp) AS total_gp,
    SUM(gp) / NULLIF(SUM(CASE WHEN booked = 1 THEN 1 ELSE 0 END), 0) AS gp_per_booked_session,
    SUM(policies) AS total_policies
FROM with_policy_ty
GROUP BY policy_type, device_type

UNION ALL

SELECT 'LY' AS yr,
    COALESCE(p.policy_type, 'No conversion') AS policy_type,
    s.device_type,
    COUNT(DISTINCT s.session_id) AS total_sessions,
    SUM(s.reached_search) AS search_sessions,
    SUM(s.reached_checkout) AS checkout_sessions,
    SUM(s.booked) AS booked_sessions,
    SUM(s.had_medical) AS medical_sessions,
    SUM(s.had_multi_search) AS multi_search_sessions,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(CASE WHEN s.booked = 1 THEN 1 ELSE 0 END), 0) AS gp_per_booked_session,
    SUM(p.policy_count) AS total_policies
FROM (
    SELECT
        w.session_id, w.device_type,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(CASE WHEN w.Multiple_search = 'Yes' THEN 1 ELSE 0 END) AS had_multi_search,
        MAX(CASE WHEN w.booking_flow_stage = 'Search' THEN 1 ELSE 0 END) AS reached_search,
        MAX(CASE WHEN w.booking_flow_stage = 'Checkout' THEN 1 ELSE 0 END) AS reached_checkout,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS booked,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) s
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = s.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY p.policy_type, s.device_type
"""
    }

    # Track 17: Multi-Search GP Impact
    tracks['multi_search_gp_impact'] = {
        'name': 'Multi-Search Session GP Impact',
        'desc': 'Do sessions where users search multiple times convert better or worse, and what is the GP impact? Breaks down by device and policy type to show whether multi-search is a sign of engaged shoppers or confused users.',
        'sql': f"""
WITH session_profile_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        MAX(CASE WHEN w.Multiple_search = 'Yes' THEN 'Multi-search' ELSE 'Single-search' END) AS search_type,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS converted,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
)
SELECT 'TY' AS yr,
    sp.search_type,
    sp.device_type,
    COUNT(DISTINCT sp.session_id) AS total_sessions,
    SUM(sp.converted) AS converted_sessions,
    SAFE_DIVIDE(SUM(sp.converted), COUNT(DISTINCT sp.session_id)) AS conversion_rate,
    SUM(p.policy_count) AS policies,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(sp.converted), 0) AS gp_per_converted_session,
    MAX(p.policy_type) AS dominant_policy_type,
    SUM(sp.had_medical) AS medical_sessions
FROM session_profile_ty sp
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = sp.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY sp.search_type, sp.device_type

UNION ALL

SELECT 'LY' AS yr, sp.search_type, sp.device_type,
    COUNT(DISTINCT sp.session_id),
    SUM(sp.converted),
    SAFE_DIVIDE(SUM(sp.converted), COUNT(DISTINCT sp.session_id)),
    SUM(p.policy_count),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(sp.converted), 0),
    MAX(p.policy_type),
    SUM(sp.had_medical)
FROM (
    SELECT w.session_id, w.device_type,
        MAX(CASE WHEN w.Multiple_search = 'Yes' THEN 'Multi-search' ELSE 'Single-search' END) AS search_type,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS had_medical,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS converted,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) sp
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = sp.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY sp.search_type, sp.device_type
"""
    }

    # Track 18: Medical Screening Funnel × Device — conversion and GP
    tracks['medical_screening_funnel'] = {
        'name': 'Medical Screening Funnel by Device',
        'desc': 'How does the medical screening step specifically affect conversion and GP by device? Compares sessions that hit the screening page vs those that did not, and tracks their conversion rate and resulting GP. Reveals if medical screening is a conversion killer on mobile.',
        'sql': f"""
WITH session_screening_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        MAX(CASE WHEN w.page_type = 'screening' THEN 1 ELSE 0 END) AS hit_screening,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS med_session,
        MAX(CASE WHEN w.booking_flow_stage = 'Search' THEN 1 ELSE 0 END) AS reached_search,
        MAX(CASE WHEN w.page_type = 'search_results' THEN 1 ELSE 0 END) AS reached_results,
        MAX(CASE WHEN w.booking_flow_stage = 'Checkout' THEN 1 ELSE 0 END) AS reached_checkout,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS booked,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
)
SELECT 'TY' AS yr,
    ss.device_type,
    CASE
        WHEN ss.hit_screening = 1 AND ss.med_session = 1 THEN 'Screening + Medical declared'
        WHEN ss.hit_screening = 1 AND ss.med_session = 0 THEN 'Screening (no medical)'
        ELSE 'No screening page'
    END AS screening_segment,
    COUNT(DISTINCT ss.session_id) AS sessions,
    SUM(ss.reached_search) AS search_sessions,
    SUM(ss.reached_results) AS results_sessions,
    SUM(ss.reached_checkout) AS checkout_sessions,
    SUM(ss.booked) AS booked_sessions,
    SAFE_DIVIDE(SUM(ss.booked), COUNT(DISTINCT ss.session_id)) AS conversion_rate,
    SUM(p.policy_count) AS policies,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp_per_policy,
    SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_price,
    SUM(CAST(p.medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_medical_premium
FROM session_screening_ty ss
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = ss.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY ss.device_type, screening_segment

UNION ALL

SELECT 'LY' AS yr, ss.device_type,
    CASE
        WHEN ss.hit_screening = 1 AND ss.med_session = 1 THEN 'Screening + Medical declared'
        WHEN ss.hit_screening = 1 AND ss.med_session = 0 THEN 'Screening (no medical)'
        ELSE 'No screening page'
    END AS screening_segment,
    COUNT(DISTINCT ss.session_id),
    SUM(ss.reached_search), SUM(ss.reached_results),
    SUM(ss.reached_checkout), SUM(ss.booked),
    SAFE_DIVIDE(SUM(ss.booked), COUNT(DISTINCT ss.session_id)),
    SUM(p.policy_count),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0)
FROM (
    SELECT w.session_id, w.device_type,
        MAX(CASE WHEN w.page_type = 'screening' THEN 1 ELSE 0 END) AS hit_screening,
        MAX(CASE WHEN w.med_session = TRUE THEN 1 ELSE 0 END) AS med_session,
        MAX(CASE WHEN w.booking_flow_stage = 'Search' THEN 1 ELSE 0 END) AS reached_search,
        MAX(CASE WHEN w.page_type = 'search_results' THEN 1 ELSE 0 END) AS reached_results,
        MAX(CASE WHEN w.booking_flow_stage = 'Checkout' THEN 1 ELSE 0 END) AS reached_checkout,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS booked,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) ss
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = ss.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY ss.device_type, screening_segment
"""
    }

    # Track 19: Cover Level Upsell from Web — what users search vs what they buy
    tracks['web_cover_level_outcome'] = {
        'name': 'Web Insurance Group to Cover Level Outcome',
        'desc': 'Joins the insurance_group seen during web sessions to the actual cover level purchased. Reveals whether users who browse on different schemes/groups end up buying higher or lower cover, and how GP differs. Identifies upsell opportunities and mismatches between web browsing and purchase.',
        'sql': f"""
WITH web_sessions_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        MAX(w.insurance_group) AS web_insurance_group,
        MAX(w.scheme_name) AS web_scheme,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.certificate_id IS NOT NULL
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
)
SELECT 'TY' AS yr,
    ws.web_insurance_group,
    ws.device_type,
    p.cover_level_name,
    p.cover_level_tier,
    p.policy_type,
    SUM(p.policy_count) AS policies,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp,
    SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_price,
    SUM(CAST(p.option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_option_premium,
    SUM(CAST(p.total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gadget_premium,
    COUNT(DISTINCT ws.session_id) AS converting_sessions
FROM web_sessions_ty ws
JOIN {P} p ON CAST(p.certificate_id AS STRING) = ws.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY ws.web_insurance_group, ws.device_type, p.cover_level_name, p.cover_level_tier, p.policy_type
HAVING ABS(SUM(p.policy_count)) >= 2

UNION ALL

SELECT 'LY' AS yr,
    ws.web_insurance_group, ws.device_type,
    p.cover_level_name, p.cover_level_tier, p.policy_type,
    SUM(p.policy_count),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    COUNT(DISTINCT ws.session_id)
FROM (
    SELECT w.session_id, w.device_type,
        MAX(w.insurance_group) AS web_insurance_group,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
      AND w.certificate_id IS NOT NULL
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
) ws
JOIN {P} p ON CAST(p.certificate_id AS STRING) = ws.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY ws.web_insurance_group, ws.device_type, p.cover_level_name, p.cover_level_tier, p.policy_type
HAVING ABS(SUM(p.policy_count)) >= 2
"""
    }

    # Track 20: Session Depth vs Policy Outcome
    tracks['session_depth_outcome'] = {
        'name': 'Session Engagement Depth vs Trading Outcome',
        'desc': 'Measures how deep into the funnel sessions go (by counting distinct page types visited) and links that to conversion and GP. Separates sessions into light browsers (1-2 pages), engaged browsers (3-4 pages), and deep explorers (5+), then shows conversion rate and GP for each depth bucket by device. Answers: are we losing money because people bounce early, or because deep-funnel users are not converting?',
        'sql': f"""
WITH session_depth_ty AS (
    SELECT
        w.session_id,
        w.device_type,
        COUNT(DISTINCT w.page_type) AS pages_visited,
        MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS converted,
        MAX(w.certificate_id) AS certificate_id
    FROM {W} w
    WHERE w.session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
      AND w.device_type IN ('mobile','computer','tablet')
    GROUP BY w.session_id, w.device_type
),
bucketed_ty AS (
    SELECT *,
        CASE
            WHEN pages_visited <= 2 THEN '1-2 pages (light)'
            WHEN pages_visited <= 4 THEN '3-4 pages (engaged)'
            ELSE '5+ pages (deep)'
        END AS depth_bucket
    FROM session_depth_ty
)
SELECT 'TY' AS yr,
    b.depth_bucket,
    b.device_type,
    COUNT(DISTINCT b.session_id) AS sessions,
    SUM(b.converted) AS converted_sessions,
    SAFE_DIVIDE(SUM(b.converted), COUNT(DISTINCT b.session_id)) AS conversion_rate,
    SUM(p.policy_count) AS policies,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS total_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0) AS avg_gp,
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(b.converted), 0) AS gp_per_converted_session
FROM bucketed_ty b
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = b.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY b.depth_bucket, b.device_type

UNION ALL

SELECT 'LY' AS yr, b.depth_bucket, b.device_type,
    COUNT(DISTINCT b.session_id),
    SUM(b.converted),
    SAFE_DIVIDE(SUM(b.converted), COUNT(DISTINCT b.session_id)),
    SUM(p.policy_count),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(p.policy_count), 0),
    SUM(CAST(p.total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(b.converted), 0)
FROM (
    SELECT sd.*,
        CASE
            WHEN sd.pages_visited <= 2 THEN '1-2 pages (light)'
            WHEN sd.pages_visited <= 4 THEN '3-4 pages (engaged)'
            ELSE '5+ pages (deep)'
        END AS depth_bucket
    FROM (
        SELECT w.session_id, w.device_type,
            COUNT(DISTINCT w.page_type) AS pages_visited,
            MAX(CASE WHEN w.page_type = 'just_booked' THEN 1 ELSE 0 END) AS converted,
            MAX(w.certificate_id) AS certificate_id
        FROM {W} w
        WHERE w.session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
          AND w.device_type IN ('mobile','computer','tablet')
        GROUP BY w.session_id, w.device_type
    ) sd
) b
LEFT JOIN {P} p ON CAST(p.certificate_id AS STRING) = b.certificate_id
    AND p.transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY b.depth_bucket, b.device_type
"""
    }

    # Track 21: Cost Decomposition — commission, NTU, IPT, UW as % of gross
    tracks['cost_decomposition'] = {
        'name': 'Cost Decomposition vs Price Growth',
        'desc': 'Breaks out commission, underwriter cost, IPT, and net GP as a percentage of total gross price paid by the customer. Compares whether each cost line grew faster or slower than the price customers paid, split by channel and policy type. Answers: is margin shrinking because costs are rising faster than revenue, or because of mix?',
        'sql': f"""
SELECT 'TY' AS yr, distribution_channel, policy_type,
    SUM(policy_count) AS policies,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) AS total_gross,
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_price,
    SUM(CAST(total_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_ipt,
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_commission,
    SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_uw_cost,
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp,
    -- As % of gross price
    SAFE_DIVIDE(SUM(CAST(total_ipt AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS ipt_pct_of_gross,
    SAFE_DIVIDE(SUM(CAST(total_paid_commission_value AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS commission_pct_of_gross,
    SAFE_DIVIDE(SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS uw_pct_of_gross,
    SAFE_DIVIDE(SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS gp_margin_pct,
    -- Discount as % of gross
    SAFE_DIVIDE(SUM(CAST(total_discount_value AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))) AS discount_pct_of_gross,
    -- Medical and gadget components
    SUM(CAST(medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_medical_premium,
    SUM(CAST(total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gadget_premium,
    SUM(CAST(option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_option_premium
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
GROUP BY distribution_channel, policy_type
UNION ALL
SELECT 'LY', distribution_channel, policy_type,
    SUM(policy_count),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)),
    SUM(CAST(total_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_paid_commission_value AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SAFE_DIVIDE(SUM(CAST(total_ipt AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SAFE_DIVIDE(SUM(CAST(total_paid_commission_value AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SAFE_DIVIDE(SUM(CAST(total_net_to_underwriter_inc_gadget AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SAFE_DIVIDE(SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SAFE_DIVIDE(SUM(CAST(total_discount_value AS FLOAT64)), SUM(CAST(total_gross_inc_ipt AS FLOAT64))),
    SUM(CAST(medical_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(total_gadget_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0),
    SUM(CAST(option_gross_inc_ipt AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
FROM {P} WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
GROUP BY distribution_channel, policy_type
"""
    }

    # Track 22: Conversion-to-GP Bridge — web traffic × conversion rate × avg GP by device
    tracks['conversion_gp_bridge'] = {
        'name': 'Traffic × Conversion × Price × GP Bridge',
        'desc': 'Decomposes the web funnel into: sessions × session-to-search rate × search-to-book rate, by device. Separately shows policy-level GP decomposition (volume × price × margin%). Answers: is it a traffic problem, a conversion problem, a price problem, or a cost problem?',
        'sql': f"""
SELECT 'TY' AS yr, 'web' AS source, device_type,
    COUNT(DISTINCT session_id) AS sessions,
    COUNT(DISTINCT visitor_id) AS visitors,
    COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END) AS search_sessions,
    COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END) AS booked_sessions,
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
        COUNT(DISTINCT session_id)
    ) AS session_to_search,
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
        COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END)
    ) AS search_to_book
FROM {W}
WHERE session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  AND device_type IN ('mobile','computer','tablet')
GROUP BY device_type

UNION ALL

SELECT 'LY', 'web', device_type,
    COUNT(DISTINCT session_id),
    COUNT(DISTINCT visitor_id),
    COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
    COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
        COUNT(DISTINCT session_id)
    ),
    SAFE_DIVIDE(
        COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
        COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END)
    )
FROM {W}
WHERE session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  AND device_type IN ('mobile','computer','tablet')
GROUP BY device_type
"""
    }

    # Track 23: Customer Type (New vs Existing) — traffic, conversion and GP
    tracks['customer_type_deep'] = {
        'name': 'Customer Type Trading',
        'desc': 'New vs Existing customer dynamics across web traffic (sessions, conversion) and policy GP by distribution channel. Answers: are we winning new customers or losing them, and how does that affect GP?',
        'sql': f"""
WITH web AS (
  SELECT 'TY' AS yr, customer_type,
      COUNT(DISTINCT session_id) AS sessions,
      COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END) AS search_sessions,
      COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END) AS booked_sessions,
      SAFE_DIVIDE(
          COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
          COUNT(DISTINCT session_id)
      ) AS session_to_search,
      SAFE_DIVIDE(
          COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
          COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END)
      ) AS search_to_book
  FROM {W}
  WHERE session_start_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  GROUP BY customer_type

  UNION ALL

  SELECT 'LY', customer_type,
      COUNT(DISTINCT session_id),
      COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
      COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
      SAFE_DIVIDE(
          COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END),
          COUNT(DISTINCT session_id)
      ),
      SAFE_DIVIDE(
          COUNT(DISTINCT CASE WHEN page_type = 'just_booked' THEN session_id END),
          COUNT(DISTINCT CASE WHEN booking_flow_stage = 'Search' THEN session_id END)
      )
  FROM {W}
  WHERE session_start_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  GROUP BY customer_type
),
pol AS (
  SELECT 'TY' AS yr, customer_type, distribution_channel,
      SUM(policy_count) AS policies,
      SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) AS gp,
      SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0) AS avg_gp
  FROM {P}
  WHERE transaction_date BETWEEN '{dp["week_start"]}' AND '{dp["yesterday"]}'
  GROUP BY customer_type, distribution_channel

  UNION ALL

  SELECT 'LY', customer_type, distribution_channel,
      SUM(policy_count),
      SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)),
      SUM(CAST(total_gross_exc_ipt_ntu_comm AS FLOAT64)) / NULLIF(SUM(policy_count), 0)
  FROM {P}
  WHERE transaction_date BETWEEN '{dp["week_start_ly"]}' AND '{dp["yesterday_ly"]}'
  GROUP BY customer_type, distribution_channel
)
SELECT 'web' AS source, yr, customer_type, CAST(NULL AS STRING) AS distribution_channel,
    sessions, search_sessions, booked_sessions, session_to_search, search_to_book,
    CAST(NULL AS INT64) AS policies, CAST(NULL AS FLOAT64) AS gp, CAST(NULL AS FLOAT64) AS avg_gp
FROM web
UNION ALL
SELECT 'policy', yr, customer_type, distribution_channel,
    CAST(NULL AS INT64), CAST(NULL AS INT64), CAST(NULL AS INT64), CAST(NULL AS FLOAT64), CAST(NULL AS FLOAT64),
    policies, gp, avg_gp
FROM pol
ORDER BY source, yr, customer_type
"""
    }

    return tracks
