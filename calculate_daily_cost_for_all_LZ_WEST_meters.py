import pandas as pd
import os
import glob

def calculate_total_cost_batch_for_zone(price_file, usage_folder, merged_folder, summary_output_file, zone_tag):
    # Load and prepare price data
    df_price = pd.read_csv(price_file)
    df_price['Settlement Point Price'] = pd.to_numeric(df_price['Settlement Point Price'], errors='coerce') / 1000
    df_price['Delivery Date'] = pd.to_datetime(df_price['Delivery Date'])
    df_price['Interval Start'] = df_price.apply(
        lambda row: row['Delivery Date'] + pd.Timedelta(hours=row['Delivery Hour'] - 1,
                                                        minutes=(row['Delivery Interval'] - 1) * 15),
        axis=1
    )
    price_df = df_price[['Interval Start', 'Settlement Point Price']]

    # Prepare folders
    os.makedirs(merged_folder, exist_ok=True)

    # Collect results
    all_costs = []

    # Match usage files that end with this zone tag
    # usage_files = glob.glob(os.path.join(usage_folder, f"*{zone_tag}.csv"))
    usage_files = [
    f for f in glob.glob(os.path.join(usage_folder, f"IntervalData*{zone_tag}.csv"))
    if os.path.isfile(f)
]
    for usage_file in usage_files:
        try:
            df_usage = pd.read_csv(usage_file)
            df_usage['USAGE_DATE'] = pd.to_datetime(df_usage['USAGE_DATE'])
            df_usage['USAGE_START_TIME'] = pd.to_timedelta(df_usage['USAGE_START_TIME'] + ":00")
            df_usage['Interval Start'] = df_usage['USAGE_DATE'] + df_usage['USAGE_START_TIME']
            df_usage['USAGE_KWH'] = pd.to_numeric(df_usage['USAGE_KWH'], errors='coerce')
            df_usage['ESIID'] = df_usage['ESIID'].astype(str).str.strip("'")

            merged_df = pd.merge(df_usage, price_df, on='Interval Start', how='inner')
            merged_df['COST'] = merged_df['USAGE_KWH'] * merged_df['Settlement Point Price']
            merged_df['ESIID'] = merged_df['ESIID'].astype(str)

            # Save merged file
            base_name = os.path.splitext(os.path.basename(usage_file))[0]
            merged_output_file = os.path.join(merged_folder, f"{base_name}_merged.csv")
            merged_df.to_csv(merged_output_file, index=False)

            # Append total cost info
            total_cost = merged_df.groupby('ESIID')['COST'].sum().reset_index()
            total_cost.columns = ['ESIID', 'Total Cost ($)']
            total_cost['Source File'] = base_name
            all_costs.append(total_cost)

            print(f"Processed: {usage_file}")

        except Exception as e:
            print(f"Error processing {usage_file}: {e}")

    # Combine and save summary
    if all_costs:
        summary_df = pd.concat(all_costs, ignore_index=True)
        summary_df.to_csv(summary_output_file, index=False)
        print(f"\nSummary saved to: {summary_output_file}")
    else:
        print("No valid usage files found or processed.")

# Example usage for LZ_WEST
calculate_total_cost_batch_for_zone(
    price_file="0706LZ_WEST.csv",
    usage_folder=".",  # folder containing the meter usage files
    merged_folder="merged_outputs_LZ_WEST",
    summary_output_file="summary_total_cost_LZ_WEST.csv",
    zone_tag="LZ_WEST"
)