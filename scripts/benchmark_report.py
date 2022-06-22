import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input_data_path",
        required=True,
        help="Path to generated reports."
    )
    
    parser.add_argument(
        "-o",
        "--final_report_path",
        required=True,
        help="Path to final report."
    )
    
    args = parser.parse_args()
    
    engine_csv = pd.read_csv(f"{args.input_data_path}dashboard-eng.csv")
    ep_csv = pd.read_csv(f"{args.input_data_path}dashboard-ep.csv")
    rocm_csv = pd.read_csv(f"{args.input_data_path}dashboard-rocm.csv")
    
    engine_csv = engine_csv[engine_csv.model_name != 'model_name']
    ep_csv = ep_csv[ep_csv.model_name != 'model_name']
    rocm_csv = rocm_csv[rocm_csv.model_name != 'model_name']
    
    merged = pd.concat([engine_csv, ep_csv,rocm_csv ])
    merged.to_csv(args.final_report_path,index=False)

if __name__ == "__main__":
    main()
