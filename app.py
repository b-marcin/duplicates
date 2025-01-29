import streamlit as st
import pandas as pd
import io

def read_csv_safely(file, **kwargs):
    """
    Safely read CSV file with error handling and flexible parsing
    Returns DataFrame and error message (if any)
    """
    try:
        # First try to sniff the CSV dialect
        sample = file.read(1024).decode('utf-8')
        file.seek(0)  # Reset file pointer
        
        # Try different CSV reading options
        try:
            df = pd.read_csv(
                file,
                on_bad_lines='warn',  # Warn about problematic lines
                encoding='utf-8',
                engine='python',  # More flexible but slower engine
                **kwargs
            )
        except Exception as e:
            # If that fails, try with C engine and error_bad_lines=False
            file.seek(0)  # Reset file pointer
            df = pd.read_csv(
                file,
                on_bad_lines='skip',  # Skip problematic lines
                encoding='utf-8',
                engine='c',  # Faster engine
                **kwargs
            )
        
        return df, None
    except Exception as e:
        return None, str(e)

def find_unique_records(df1, df2):
    """
    Find records that are in df1 but not in df2 and vice versa
    Returns two dataframes: unique_in_df1, unique_in_df2
    """
    # Convert dataframes to sets of tuples for comparison
    df1_records = set(df1.apply(tuple, axis=1))
    df2_records = set(df2.apply(tuple, axis=1))
    
    # Find unique records
    unique_in_df1 = df1_records - df2_records
    unique_in_df2 = df2_records - df1_records
    
    # Convert back to dataframes
    unique_df1 = pd.DataFrame(list(unique_in_df1), columns=df1.columns)
    unique_df2 = pd.DataFrame(list(unique_in_df2), columns=df2.columns)
    
    return unique_df1, unique_df2

def main():
    st.title("CSV File Comparison Tool")
    st.write("Upload two CSV files to find unique records in each file.")
    
    # Add CSV parsing options
    st.sidebar.header("CSV Parsing Options")
    delimiter = st.sidebar.text_input("Delimiter", ",")
    skip_rows = st.sidebar.number_input("Skip Rows", 0)
    
    # File uploaders
    file1 = st.file_uploader("Upload first CSV file", type=['csv'])
    file2 = st.file_uploader("Upload second CSV file", type=['csv'])
    
    if file1 and file2:
        # Read CSV files with error handling
        df1, error1 = read_csv_safely(file1, sep=delimiter, skiprows=skip_rows)
        if error1:
            st.error(f"Error reading first file: {error1}")
            # Display first few lines of the file for debugging
            file1.seek(0)
            st.text("First few lines of file 1:")
            st.code(file1.read().decode('utf-8')[:500])
            return
            
        df2, error2 = read_csv_safely(file2, sep=delimiter, skiprows=skip_rows)
        if error2:
            st.error(f"Error reading second file: {error2}")
            # Display first few lines of the file for debugging
            file2.seek(0)
            st.text("First few lines of file 2:")
            st.code(file2.read().decode('utf-8')[:500])
            return
        
        # Display file information
        st.write("### File Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("First File:")
            st.write(f"- Rows: {len(df1)}")
            st.write(f"- Columns: {len(df1.columns)}")
            st.write("- Column names:", df1.columns.tolist())
            
        with col2:
            st.write("Second File:")
            st.write(f"- Rows: {len(df2)}")
            st.write(f"- Columns: {len(df2.columns)}")
            st.write("- Column names:", df2.columns.tolist())
        
        # Display sample data
        st.write("### Sample Data (First 5 rows)")
        col1, col2 = st.columns(2)
        with col1:
            st.write("First File:")
            st.dataframe(df1.head())
        with col2:
            st.write("Second File:")
            st.dataframe(df2.head())
        
        # Check if columns match
        if set(df1.columns) != set(df2.columns):
            st.warning("Warning: The columns in both files don't match!")
            # Option to proceed anyway
            if not st.checkbox("Proceed with comparison anyway"):
                return
        
        # Compare files
        if st.button("Compare Files"):
            unique_df1, unique_df2 = find_unique_records(df1, df2)
            
            st.write("### Results")
            st.write(f"Records unique to first file: {len(unique_df1)}")
            st.write(f"Records unique to second file: {len(unique_df2)}")
            
            # Display unique records
            if len(unique_df1) > 0:
                st.write("#### Unique records in first file:")
                st.dataframe(unique_df1)
            
            if len(unique_df2) > 0:
                st.write("#### Unique records in second file:")
                st.dataframe(unique_df2)
            
            # Download buttons for unique records
            if len(unique_df1) > 0:
                csv1 = unique_df1.to_csv(index=False)
                st.download_button(
                    label="Download unique records from first file",
                    data=csv1,
                    file_name="unique_records_file1.csv",
                    mime="text/csv"
                )
            
            if len(unique_df2) > 0:
                csv2 = unique_df2.to_csv(index=False)
                st.download_button(
                    label="Download unique records from second file",
                    data=csv2,
                    file_name="unique_records_file2.csv",
                    mime="text/csv"
                )
            
            # Combined unique records
            if st.button("Combine unique records"):
                combined_unique = pd.concat([unique_df1, unique_df2], ignore_index=True)
                st.write("#### Combined unique records:")
                st.dataframe(combined_unique)
                
                # Download combined unique records
                csv_combined = combined_unique.to_csv(index=False)
                st.download_button(
                    label="Download combined unique records",
                    data=csv_combined,
                    file_name="combined_unique_records.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()