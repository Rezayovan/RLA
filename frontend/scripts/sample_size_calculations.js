export function calculate_bravo_sample_size(num_ballots, risk_limit, v_w, v_l) {
    let asn = 0;

    if (v_w > v_l) {
        try {
            const s_w = v_w / (v_w + v_l);

            const z_w = Math.log(2.0 * s_w);
            const z_l = 2.0 * (1 - s_w) > 0 ? Math.log(2.0 * (1 - s_w)) : 0;

            const n_wl = v_w + v_l;

            const p_w = v_w / n_wl;
            const p_l = v_l / n_wl;

            const p = n_wl / num_ballots;

            asn = Math.ceil((Math.log(1.0 / risk_limit) + (z_w / 2.0)) / (p * ((p_w * z_w) + (p_l * z_l))));
        }
        catch (e) {
            asn = 0;
            console.log("BRAVO sample size could not be calculated due to an error:", e);
        }
    }
    return asn
}

export function calculate_super_simple_sample_size(num_ballots, risk_limit, v_w, v_l, inflation_rate, tolerance) {
    let result = 0;
    let diluted_margin = 0;
    let rho = 0;
    try {
        diluted_margin = (v_w - v_l) / num_ballots;
        rho = (-Math.log(risk_limit)) / ((1 / (2 * inflation_rate)) + (tolerance * Math.log(1 - (1 / (2 * inflation_rate)))));
        result = Math.ceil(rho / diluted_margin);
    }
    catch (e) {
        result = 0;
        console.log("Super-simple sample size could not be calculated due to an error:", e);
    }

    return result;
}
