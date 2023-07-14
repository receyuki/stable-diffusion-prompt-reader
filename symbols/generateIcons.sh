cp -r original gray
find ./gray/ -name "*.svg" | xargs sed -i "" 's/\(.*\)\(\/><\/svg>\)/\1 fill="#8e8e93"\2/' 
find ./gray/ -name "*.svg" | xargs -I {} bash -c 'mkdir -p $(dirname png/{}) && cairosvg {} -s 4 -o png/$(basename {} .svg).png'
find ./png/ -name "*.png" | xargs -I {} bash -c 'convert {} -matte -channel A +level 0,50% +channel png/$(basename {} .png)_alpha.png'

