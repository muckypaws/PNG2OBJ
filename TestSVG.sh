#!/bin/bash

PNGTestFile="./JSWStride"
OUTDir="$PWD/SVGTests"

# Test Script for SVG Generation Tests
# All Output to Directory ./SVGTests

if [ ! -d $OUTDir ]
then
    echo "$OUTDir Directory not present"
    echo "Creating $OUTDir"
    mkdir "$OUTDir"
fi

if [ ! -f "$PNGTestFile.png" ]
then
    echo "Failed to find test PNG File: $PNGTestFile.png"
    echo "Quitting.../n"
    exit
fi




# Test Basic PNG To SVG Functionality

./PNG2ObjV3.py -svg -svgopen $PNGTestFile

./PNG2ObjV3.py -svg -svgopen $PNGTestFile

./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestDefaults $PNGTestFile

./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestDefaultsCircle -svgrpx 100 -svgrpy 100 $PNGTestFile

./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestDefaultsSquare -svgrpx 0 -svgrpy 0 $PNGTestFile

./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTable -el "#000000" -svgrpx 0 -svgrpy 0 $PNGTestFile

./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTablePixelSize -el "#000000" -svgrpx 0 -svgrpy 0 -svgpw 10 -svgph 15 $PNGTestFile

./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableOutline -el "#000000" -svgrpx 0 -svgrpy 0 -outline $PNGTestFile

# mbw and mbh ignored for basic PNG Conversion.
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableMinimumBorder -el "#000000" -svgrpx 0 -svgrpy 0 -mbw 17 $PNGTestFile

# Test Frames for Crafting
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableF400 -el "#000000" -svgrpx 0 -svgrpy 0 -f400 -ugc $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableF400Outline -el "#000000" -svgrpx 0 -svgrpy 0 -f400 -outline $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableF400OutlinewithPNG -el "#000000" -svgrpx 0 -svgrpy 0 -f400 -outline -svgaddpng $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableF400withPNG -el "#000000" -svgrpx 0 -svgrpy 0 -f400 -svgaddpng $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableF400withPNGIllusion -el "#000000" -svgrpx 20 -svgrpy 20 -f400 -svgaddpng -illusion $PNGTestFile

# Test Optical Illusion Generation
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionDefault -el "#000000" -illusion $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionDefaultWithPNG -el "#000000" -illusion -svgaddpng $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionDefaultWithPNGGridColours -el "#000000" -illusion -svgaddpng -ugc $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionNewTable -el "#000000" -illusion -ict "#D93C41" "#781314" "#3F53FF" "#020078" -ugc $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionNewTableWithPNG -el "#000000" -illusion -ict "#D93C41" "#781314" "#3F53FF" "#020078" -ugc -svgaddpng $PNGTestFile

./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionDefaultWithCircle -el "#000000" -illusion -ilc $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionDefaultWithCircleAndPNG -el "#000000" -illusion -ilc -svgaddpng $PNGTestFile
./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionDefaultWithCircleAndPNGGridColours -el "#000000" -illusion -ilc -svgaddpng -ugc $PNGTestFile

./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionDefaultStreak5 -el "#000000" -illusion -streak 8 $PNGTestFile

./PNG2ObjV3.py -svg -svgopen -outfile $OUTDir/SVGTestExcludeColourTableIllusionDefaultStreak5 -el "#000000" -illusion -stmax 8 $PNGTestFile

