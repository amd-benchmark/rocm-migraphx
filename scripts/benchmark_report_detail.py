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
    detail_csv = pd.read_csv(args.input_data_path)
    detail_csv = detail_csv[detail_csv.engine != 'engine']
    detail_csv = detail_csv[["model_name","engine","version","providers","device","precision","optimizer","io_binding","inputs","threads","batch_size","sequence_length","average_latency_ms"]]
    detail_csv.sort_values(["model_name", "batch_size", "sequence_length"],
                    axis = 0, ascending = True,
                    inplace = True,
                    na_position = "first")
    detail_csv.to_csv(args.final_report_path,index=False)
if __name__ == "__main__":
    main()