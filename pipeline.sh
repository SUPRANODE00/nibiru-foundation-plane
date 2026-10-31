#!/usr/bin/env bash
# Production Signal Processing Pipeline Optimizer

BAND="2.45"
BW="20"
SOC_THRESHOLD="20.0"

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  --band VALUE          Set RF Envelope Carrier Band in GHz (Default: 2.45)"
    echo "  --bw VALUE            Set Bandwidth in MHz (Default: 20)"
    echo "  --soc-threshold VALUE Set critical SOC safety floor percentage (Default: 20.0)"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --band) BAND="$2"; shift 2 ;;
        --bw) BW="$2"; shift 2 ;;
        --soc-threshold) SOC_THRESHOLD="$2"; shift 2 ;;
        -h|--help) show_help ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

cat /dev/stdin | \
sed -E 's/"E": *([0-9.-]+)/"E_vector": \1/g' | \
sed -E 's/"N": *([0-9.-]+)/"N_vector": \1/g' | \
awk -v band="$BAND" -v bw="$BW" -v floor="$SOC_THRESHOLD" '
BEGIN {
    FS = "[:,{} \t\"]+";
    SOC = 100.0;
    RF_Noise_Floor = -95.0;
    print "VECTOR_TYPE\tRAW_VALUE\tTUNNEL_SNR_DB\tADAPTIVE_SOC\tSTATUS"
}
{
    for (i = 1; i <= NF; i++) {
        if ($i == "E_vector" || $i == "N_vector") {
            v_type = ($i == "E_vector") ? "East-Axis" : "North-Axis";
            v_val = $(i+1);
            
            path_loss = 20 * (log(band * 1000) / log(10)) - 27.55;
            signal_power = v_val * (bw / 10);
            snr = signal_power - RF_Noise_Floor - path_loss;
            
            drain = (v_val < 0) ? (v_val * -0.15) : 1.0;
            SOC -= drain;
            
            status = "NOMINAL";
            if (SOC <= (floor + 20.0)) { status = "WARNING_ZONE"; }
            if (SOC <= (floor + 5.0))  { status = "SOFT_FLOOR"; }
            if (SOC <= floor) { 
                SOC = floor; 
                status = "CRITICAL_LIMIT"; 
            }
            printf "%s\t%.4f\t%.2f\t%.1f%%\t%s\n", v_type, v_val, snr, SOC, status;
        }
    }
}
'
