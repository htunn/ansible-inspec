#!/bin/bash
# Example: Convert InSpec Profile to Ansible Collection
#
# This script demonstrates how to convert an InSpec compliance profile
# into an Ansible collection with full support for custom resources.

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}InSpec to Ansible Collection Converter${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
PROFILE_PATH="${1:-examples/profiles/basic-compliance}"
OUTPUT_DIR="${2:-./collections}"
NAMESPACE="${3:-example}"
COLLECTION_NAME="${4:-basic_compliance}"

echo -e "${GREEN}Configuration:${NC}"
echo "  Profile: $PROFILE_PATH"
echo "  Output: $OUTPUT_DIR"
echo "  Namespace: $NAMESPACE"
echo "  Collection: $COLLECTION_NAME"
echo ""

# Check if profile exists
if [ ! -d "$PROFILE_PATH" ]; then
    echo -e "${YELLOW}Error: Profile not found: $PROFILE_PATH${NC}"
    echo ""
    echo "Usage: $0 [profile_path] [output_dir] [namespace] [collection_name]"
    echo ""
    echo "Example:"
    echo "  $0 ./my-profile ./collections myorg compliance"
    exit 1
fi

# Check if ansible-inspec is installed
if ! command -v ansible-inspec &> /dev/null; then
    echo -e "${YELLOW}Error: ansible-inspec not found${NC}"
    echo "Install with: pip install ansible-inspec"
    exit 1
fi

echo -e "${BLUE}Step 1: Analyzing InSpec profile...${NC}"
echo ""

# Show profile structure
echo "Profile structure:"
tree -L 2 "$PROFILE_PATH" 2>/dev/null || find "$PROFILE_PATH" -maxdepth 2 -type f -o -type d

echo ""
echo -e "${BLUE}Step 2: Converting profile to Ansible collection...${NC}"
echo ""

# Run conversion
ansible-inspec convert "$PROFILE_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --namespace "$NAMESPACE" \
  --collection-name "$COLLECTION_NAME"

COLLECTION_PATH="$OUTPUT_DIR/ansible_collections/$NAMESPACE/$COLLECTION_NAME"

if [ ! -d "$COLLECTION_PATH" ]; then
    echo -e "${YELLOW}Error: Collection not created${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 3: Building Ansible collection...${NC}"
echo ""

cd "$COLLECTION_PATH"

# Build the collection
ansible-galaxy collection build

COLLECTION_FILE=$(ls -t *.tar.gz 2>/dev/null | head -1)

if [ -z "$COLLECTION_FILE" ]; then
    echo -e "${YELLOW}Error: Collection build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Collection built: $COLLECTION_FILE${NC}"

echo ""
echo -e "${BLUE}Step 4: Collection structure:${NC}"
echo ""

tree -L 3 . 2>/dev/null || find . -maxdepth 3 -type f -o -type d

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Conversion Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Collection location:"
echo "  $COLLECTION_PATH"
echo ""
echo "Collection file:"
echo "  $COLLECTION_PATH/$COLLECTION_FILE"
echo ""
echo "Next steps:"
echo ""
echo "1. Install the collection:"
echo "   ansible-galaxy collection install $COLLECTION_PATH/$COLLECTION_FILE"
echo ""
echo "2. List installed collections:"
echo "   ansible-galaxy collection list | grep $NAMESPACE"
echo ""
echo "3. Create a playbook:"
echo "   cat > compliance-check.yml << 'EOF'"
echo "   - name: Run compliance checks"
echo "     hosts: all"
echo "     become: true"
echo "     roles:"
echo "       - $NAMESPACE.$COLLECTION_NAME.example"
echo "   EOF"
echo ""
echo "4. Run compliance checks:"
echo "   ansible-playbook compliance-check.yml -i inventory.yml"
echo ""
echo "5. Or use the included playbook:"
echo "   ansible-playbook $NAMESPACE.$COLLECTION_NAME.compliance_check -i inventory.yml"
echo ""

# Show roles created
echo -e "${BLUE}Roles created:${NC}"
if [ -d "roles" ]; then
    ls -1 roles/
else
    echo "  (none)"
fi

echo ""

# Show custom resources if any
if [ -d "files/libraries" ] && [ "$(ls -A files/libraries 2>/dev/null)" ]; then
    echo -e "${YELLOW}Custom resources detected:${NC}"
    ls -1 files/libraries/
    echo ""
    echo -e "${YELLOW}Note: Custom resources require InSpec to be installed${NC}"
    echo "Install with: brew install chef/chef/inspec"
    echo ""
fi

echo -e "${GREEN}Documentation:${NC}"
echo "  README: $COLLECTION_PATH/README.md"
echo "  Docs: $COLLECTION_PATH/docs/"
echo ""
