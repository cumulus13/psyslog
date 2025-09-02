import re
from datetime import datetime

def format_syslog_datetime(syslog_message, target_year=2025):
    """
    Extract datetime dari syslog message dan format ke YYYY:MM:DD HH:MM:SS
    
    Args:
        syslog_message (str): Syslog message string
        target_year (int): Tahun yang akan digunakan (default: 2025)
    
    Returns:
        str: Formatted datetime atau None jika tidak match
    """
    
    # Regex pattern untuk extract datetime dari syslog
    pattern = r'<\d+>\s*([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})'
    
    match = re.search(pattern, syslog_message)
    
    if not match:
        return None
    
    month_str = match.group(1)
    day_str = match.group(2).zfill(2)  # Pad dengan 0 jika perlu
    time_str = match.group(3)
    
    # Mapping bulan ke angka
    month_map = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    month_num = month_map.get(month_str)
    
    if not month_num:
        return None
    
    # Format ke YYYY:MM:DD HH:MM:SS
    formatted_datetime = f"{target_year}:{month_num}:{day_str} {time_str}"
    
    return formatted_datetime

# CONTOH PENGGUNAAN

# Test data
test_messages = [
    "<11> Sep  3 00:04:47 LIC-X TEST_TAG: TEST_MESSAGE_006",
    "<11>Sep  3 00:04:47 LIC-X TEST_TAG: TEST_MESSAGE_006",
    "<134>Jan 15 14:32:01 server01 kernel: message",
    "<33>Dec  8 23:59:59 host01 app: another message"
]

print("=== HASIL FORMATTING ===")
for message in test_messages:
    result = format_syslog_datetime(message)
    print(f"Input:  {message}")
    print(f"Output: {result}")
    print("-" * 50)

# VERSI DENGAN datetime OBJECT
def format_syslog_datetime_advanced(syslog_message, target_year=2025):
    """
    Versi advanced menggunakan datetime object untuk validasi
    """
    pattern = r'<\d+>\s*([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})'
    match = re.search(pattern, syslog_message)
    
    if not match:
        return None
    
    month_str = match.group(1)
    day_str = match.group(2)
    time_str = match.group(3)
    
    try:
        # Parse menggunakan datetime
        datetime_str = f"{target_year} {month_str} {day_str} {time_str}"
        dt_obj = datetime.strptime(datetime_str, "%Y %b %d %H:%M:%S")
        
        # Format ke target format
        formatted = dt_obj.strftime("%Y:%m:%d %H:%M:%S")
        return formatted
        
    except ValueError as e:
        print(f"Error parsing datetime: {e}")
        return None

print("\n=== VERSI ADVANCED (dengan validasi) ===")
for message in test_messages:
    result = format_syslog_datetime_advanced(message)
    print(f"Input:  {message}")
    print(f"Output: {result}")
    print("-" * 50)

# FUNGSI UNTUK BATCH PROCESSING
def process_syslog_file(file_path, output_file=None):
    """
    Process file syslog dan format semua datetime
    """
    results = []
    
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    formatted = format_syslog_datetime(line)
                    if formatted:
                        results.append({
                            'line_num': line_num,
                            'original': line,
                            'formatted_datetime': formatted
                        })
        
        if output_file:
            with open(output_file, 'w') as f:
                for item in results:
                    f.write(f"Line {item['line_num']}: {item['formatted_datetime']}\n")
        
        return results
        
    except FileNotFoundError:
        print(f"File {file_path} tidak ditemukan")
        return []

# CONTOH PENGGUNAAN UNTUK SINGLE STRING
if __name__ == "__main__":
    # Contoh single conversion
    syslog_msg = "<11> Sep  3 00:04:47 LIC-X TEST_TAG: TEST_MESSAGE_006"
    formatted = format_syslog_datetime(syslog_msg)
    print(f"\nHASIL AKHIR [1]: {formatted}")
    
    syslog_msg1 = "<11>Sep  3 00:04:47 LIC-X TEST_TAG: TEST_MESSAGE_006"
    formatted = format_syslog_datetime(syslog_msg1)
    print(f"\nHASIL AKHIR [2]: {formatted}")
    
    # Expected output: 2025:09:03 00:04:47