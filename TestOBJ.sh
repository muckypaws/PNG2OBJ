#!/bin/bash

PNGTestFile1="./JSWStride.png"
PNGTestFile2="./JSWStrideSingle.png"
PNGTestFile3="./PlatformWilly.png"

OUTDir="./OBJTests"

# Test Script for SVG Generation Tests
# All Output to Directory ./SVGTests

if [ ! -d $OUTDir ]
then
    echo "$OUTDir Directory not present"
    echo "Creating $OUTDir"
    mkdir "$OUTDir"
fi

if [ ! -f "$PNGTestFile2" ]
then
    echo "Failed to find test PNG File: $PNGTestFile2"
    echo "Quitting.../n"
    exit
fi


# Test Basic PNG To OBJ Functionality
./PNG2ObjV3.py $PNGTestFile1

# Write Output to New Location
./PNG2ObjV3.py $PNGTestFile2 -outfile $OUTDir/JSWTest02

# Test Basic PNG To OBJ Functionality with Material File
./PNG2ObjV3.py $PNGTestFile2 -outfile $OUTDir/JSWTest03 --mtl

# Test Basic PNG To OBJ Functionality with Material File and no Frame
./PNG2ObjV3.py $PNGTestFile2 -outfile $OUTDir/JSWTest04 --mtl -nf

# Test Basic PNG To OBJ Functionality with Material File and no Frame
./PNG2ObjV3.py $PNGTestFile2 -outfile $OUTDir/JSWTest05 --mtl -nf -db

# Test Basic PNG To OBJ Functionality exclude Black and bright green
./PNG2ObjV3.py $PNGTestFile3 -outfile $OUTDir/JSWTest06 --mtl -nf -el \#000000 \#00ff00

# Test Basic PNG To OBJ Functionality Sort Colours Low to High
./PNG2ObjV3.py $PNGTestFile3 -outfile $OUTDir/JSWTest07 --mtl -nf -s --layered

# Test Basic PNG To OBJ Functionality Sort Colours Low to High
PARMS="-outfile $OUTDir/JSWTest08 --mtl -nf -rs"
./PNG2ObjV3.py $PNGTestFile3 $PARMS

# Test Basic PNG To OBJ Functionality Process Colours List
PARMS="-outfile $OUTDir/JSWTest09 --mtl -nf --processcolours #bdbdbd #bf00bf --layered"
./PNG2ObjV3.py $PNGTestFile3 $PARMS

# Test Basic PNG To OBJ Functionality Process Colours List
PARMS="--processcolours #bf00bf #bdbdbd -m -outfile $OUTDir/JSWTest10 -nf --layered"
./PNG2ObjV3.py $PNGTestFile3 $PARMS

# Test Basic PNG To OBJ Functionality Background Height
./PNG2ObjV3.py $PNGTestFile3 -outfile $OUTDir/JSWTest11 --mtl -s -bgh 2.0 -el \#000000

# Test Basic PNG To OBJ Functionality Background Height
./PNG2ObjV3.py $PNGTestFile2 -outfile $OUTDir/JSWTest12 --mtl -bgh 2.0 


# Test Basic PNG To OBJ Functionality Background Height
./PNG2ObjV3.py $PNGTestFile2 -outfile $OUTDir/JSWTest13 --mtl -bgh 2.0 -lm 5.0  --layered