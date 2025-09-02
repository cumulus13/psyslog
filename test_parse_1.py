# REGEX PATTERNS
"""
# 1. Basic - hanya ambil datetime part
(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}

# 2. More specific - dengan named groups
(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})

# 3. Complete pattern - extract dari full syslog message
<\d+>\s*(?P<datetime>(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})

# 4. Flexible - handle dengan atau tanpa space setelah priority
<\d+>\s*(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?P<day>\d{1,2})\s+(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})

# 5. Ultra flexible - untuk semua variasi spacing
<\d+>\s*([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})

# CONTOH PENGGUNAAN DALAM BERBAGAI BAHASA:

"""# Python
import re

pattern = r'<\d+>\s*(?P<datetime>([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2}))'
text1 = "<11> Sep  3 00:04:47 LIC-X TEST_TAG: TEST_MESSAGE_006"
text2 = "<11>Sep  3 00:04:47 LIC-X TEST_TAG: TEST_MESSAGE_006"

match1 = re.search(pattern, text1)
match2 = re.search(pattern, text2)

if match1:
    print(f"Datetime 1: {match1.group('datetime')}")  # Output: Sep  3 00:04:47
if match2:
    print(f"Datetime 2: {match2.group('datetime')}")  # Output: Sep  3 00:04:47

# JavaScript
# const pattern = /<\d+>\s*([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})/;
# const text1 = "<11> Sep  3 00:04:47 LIC-X TEST_TAG: TEST_MESSAGE_006";
# const match1 = text1.match(pattern);
# if (match1) {
#     console.log(`Datetime: ${match1[1]} ${match1[2]} ${match1[3]}`); // Sep 3 00:04:47
# }

# # PHP
# $pattern = '/<\d+>\s*([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})/';
# $text1 = "<11> Sep  3 00:04:47 LIC-X TEST_TAG: TEST_MESSAGE_006";
# if (preg_match($pattern, $text1, $matches)) {
#     echo "Datetime: " . $matches[1] . " " . $matches[2] . " " . $matches[3]; // Sep 3 00:04:47
# }

# # Bash/grep
# echo "<11> Sep  3 00:04:47 LIC-X TEST_TAG: TEST_MESSAGE_006" | grep -oP '<\d+>\s*\K[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}'