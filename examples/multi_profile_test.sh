#!/bin/bash
# Multi-profile compliance testing using Chef Supermarket
# 
# This script demonstrates how to run multiple compliance profiles
# from Chef Supermarket against your infrastructure.
#
# Usage:
#   ./multi_profile_test.sh inventory.yml

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <inventory.yml>"
    echo ""
    echo "Example:"
    echo "  $0 inventory.yml"
    exit 1
fi

INVENTORY=$1

# Check if inventory file exists
if [ ! -f "$INVENTORY" ]; then
    echo -e "${RED}Error: Inventory file not found: $INVENTORY${NC}"
    exit 1
fi

# Check if ansible-inspec is installed
if ! command -v ansible-inspec &> /dev/null; then
    echo -e "${RED}Error: ansible-inspec not found${NC}"
    echo "Install with: pip install ansible-inspec"
    exit 1
fi

# Check if InSpec is installed
if ! command -v inspec &> /dev/null; then
    echo -e "${RED}Error: InSpec not found${NC}"
    echo "Install with:"
    echo "  macOS:  brew install chef/chef/inspec"
    echo "  Linux:  curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Multi-Profile Compliance Testing${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Inventory: ${GREEN}$INVENTORY${NC}"
echo ""

# Define profiles to test
declare -a PROFILES=(
    "dev-sec/linux-baseline"
    "dev-sec/ssh-baseline"
)

# Optional profiles (add as needed)
# Uncomment the ones you want to test
# declare -a OPTIONAL_PROFILES=(
#     "dev-sec/apache-baseline"
#     "dev-sec/mysql-baseline"
#     "dev-sec/nginx-baseline"
#     "dev-sec/postgres-baseline"
#     "cis-docker-benchmark"
# )

# Results directory
RESULTS_DIR="compliance-results-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}Results directory: ${GREEN}$RESULTS_DIR${NC}"
echo ""

# Track success/failure
TOTAL_PROFILES=0
PASSED_PROFILES=0
FAILED_PROFILES=0

# Run each profile
for profile in "${PROFILES[@]}"; do
    TOTAL_PROFILES=$((TOTAL_PROFILES + 1))
    
    # Clean profile name for filename
    profile_filename=$(echo "$profile" | tr '/' '_')
    
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Testing Profile:${NC} ${GREEN}$profile${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Run the profile
    if ansible-inspec exec "$profile" \
        --supermarket \
        -i "$INVENTORY" \
        --reporter cli "json:$RESULTS_DIR/${profile_filename}.json"; then
        
        PASSED_PROFILES=$((PASSED_PROFILES + 1))
        echo -e "${GREEN}✓ Profile passed${NC}"
    else
        FAILED_PROFILES=$((FAILED_PROFILES + 1))
        echo -e "${RED}✗ Profile failed${NC}"
    fi
    
    echo ""
done

# Print summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}COMPLIANCE TESTING SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Total Profiles Tested: ${BLUE}$TOTAL_PROFILES${NC}"
echo -e "Passed:               ${GREEN}$PASSED_PROFILES${NC}"
echo -e "Failed:               ${RED}$FAILED_PROFILES${NC}"
echo ""
echo -e "Results saved to: ${GREEN}$RESULTS_DIR/${NC}"
echo ""

# List result files
echo -e "${BLUE}Result Files:${NC}"
for file in "$RESULTS_DIR"/*.json; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo -e "  • $(basename "$file") ${YELLOW}($size)${NC}"
    fi
done
echo ""

# Exit with error if any profile failed
if [ $FAILED_PROFILES -gt 0 ]; then
    echo -e "${RED}⚠ Some compliance profiles failed${NC}"
    exit 1
else
    echo -e "${GREEN}✓ All compliance profiles passed${NC}"
    exit 0
fi
