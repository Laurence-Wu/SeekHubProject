#!/usr/bin/env python3
"""
Year Traversal Script for Z-Library Book Search

This script loops through years 2000 to 2025 and runs the unprocessed JSON generator
for each year using the update_preferred_year function from config.py.
"""

import subprocess
import sys
import os
import time
from zlibraryCrowler.config import update_preferred_year, PREFERRED_YEAR

def run_unprocessed_json_generator():
    """
    Run the unprocessed JSON generator script.
    
    Returns:
        bool: True if the script ran successfully, False otherwise
    """
    try:
        # Get the path to the unprocessed JSON generator
        script_path = os.path.join(os.path.dirname(__file__), 'unprocessesd_json_generator.py')
        
        # Set up environment to include current directory in Python path
        env = os.environ.copy()
        current_dir = os.path.dirname(__file__)
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{current_dir}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = current_dir
        
        # Run the script using Python with proper environment
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, 
                              text=True, 
                              timeout=1500,  # 5 minute timeout
                              env=env,      # Pass the modified environment
                              cwd=current_dir)  # Set working directory
        
        # Print output for debugging
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Script timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running unprocessed JSON generator: {e}")
        return False

def main():
    """
    Main function to loop through years 2000-2025 and run the JSON generator for each year.
    """
    print("="*80)
    print("YEAR TRAVERSAL SCRIPT FOR Z-LIBRARY BOOK SEARCH")
    print("="*80)
    print(f"Current preferred year in config: {PREFERRED_YEAR}")
    print("Starting year traversal from 2000 to 2025...")
    print("="*80)
    
    # Store the original year to restore later
    original_year = PREFERRED_YEAR
    
    # Statistics tracking
    successful_years = []
    failed_years = []
    total_start_time = time.time()
    
    # Loop through years 2000 to 2025
    for year in range(2000, 2026):  # 2026 because range is exclusive
        print(f"\n{'='*60}")
        print(f"PROCESSING YEAR: {year}")
        print(f"{'='*60}")
        
        year_start_time = time.time()
        
        # Update the preferred year in config
        print(f"🔄 Updating preferred year to {year}...")
        update_success = update_preferred_year(year)
        
        if not update_success:
            print(f"❌ Failed to update preferred year to {year}")
            failed_years.append(year)
            continue
        
        print(f"✅ Successfully updated preferred year to {year}")
        
        # Run the unprocessed JSON generator
        print(f"🚀 Running unprocessed JSON generator for year {year}...")
        generator_success = run_unprocessed_json_generator()
        
        year_end_time = time.time()
        year_duration = year_end_time - year_start_time
        
        if generator_success:
            print(f"✅ Successfully completed processing for year {year}")
            print(f"⏱️  Year {year} processing time: {year_duration:.2f} seconds")
            successful_years.append(year)
        else:
            print(f"❌ Failed to process year {year}")
            failed_years.append(year)
        
        # Add a small delay between years to avoid overwhelming the system
        print(f"⏸️  Waiting 3 seconds before next year...")
        time.sleep(3)
    
    # Restore original year
    print(f"\n{'='*60}")
    print("RESTORING ORIGINAL CONFIGURATION")
    print(f"{'='*60}")
    print(f"🔄 Restoring original preferred year to {original_year}...")
    restore_success = update_preferred_year(original_year)
    if restore_success:
        print(f"✅ Successfully restored preferred year to {original_year}")
    else:
        print(f"❌ Failed to restore preferred year to {original_year}")
    
    # Print final statistics
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    print(f"\n{'='*80}")
    print("YEAR TRAVERSAL COMPLETED")
    print(f"{'='*80}")
    print(f"📊 STATISTICS:")
    print(f"   • Total years processed: {len(successful_years) + len(failed_years)}")
    print(f"   • Successful years: {len(successful_years)}")
    print(f"   • Failed years: {len(failed_years)}")
    print(f"   • Success rate: {len(successful_years)/(len(successful_years) + len(failed_years))*100:.1f}%")
    print(f"   • Total processing time: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
    print(f"   • Average time per year: {total_duration/(len(successful_years) + len(failed_years)):.2f} seconds")
    
    if successful_years:
        print(f"\n✅ SUCCESSFUL YEARS: {successful_years}")
    
    if failed_years:
        print(f"\n❌ FAILED YEARS: {failed_years}")
    
    print(f"\n🏁 Year traversal script completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user (Ctrl+C)")
        print("🔄 Attempting to restore original configuration...")
        # Try to restore original year if interrupted
        try:
            from zlibraryCrowler.config import PREFERRED_YEAR
            update_preferred_year(PREFERRED_YEAR)
            print("✅ Configuration restored")
        except:
            print("❌ Could not restore configuration")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error occurred: {e}")
        sys.exit(1)