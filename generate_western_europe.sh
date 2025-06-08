#!/bin/bash

echo "🗺️  Generating Western Europe focused campaign map..."
echo "   This will focus on France, Spain, Britain, Germany, and Italy"
echo "   Excludes: Eastern Europe, Russia, Scandinavia"
echo ""

# Western Europe bounds: Atlantic to Poland, North Africa to Britain
# This will make Spanish cities appear in proper relative positions
python tools/tile_terrain_generator.py \
  --bounds -10,36,20,60 \
  --zoom 9 \
  --hex-size-km 25 \
  -o game/campaign/western_europe.json \
  --save-image

echo ""
echo "✅ Generated western_europe.json"
echo "   To use this map, rename it to medieval_europe.json"
echo "   Bounds: -10°W to 20°E, 36°N to 60°N (focuses on Western Europe)"