#!/bin/bash
OPENHAB_DIR=/etc/openhab2

BACKUP_DIR=./backup
BACKUP_ITEMS_DIR=$BACKUP_DIR/items
BACKUP_SITEMAPS_DIR=$BACKUP_DIR/sitemaps
BACKUP_THINGS_DIR=$BACKUP_DIR/things

DESC_ITEMS_DIR=$OPENHAB_DIR/items
DESC_SITEMAPS_DIR=$OPENHAB_DIR/sitemaps
DESC_THINGS_DIR=$OPENHAB_DIR/things

SRC_ITEMS_DIR=./items
SRC_SITEMAPS_DIR=./sitemaps
SRC_THINGS_DIR=./things

mkdir -p $BACKUP_DIR
cp $DESC_ITEMS_DIR/* $BACKUP_ITEMS_DIR
cp $DESC_SITEMAPS_DIR/* $BACKUP_SITEMAPS_DIR
cp $DESC_THINGS_DIR/* $BACKUP_THINGS_DIR

rm -rf $DESC_ITEMS_DIR/*
rm -rf $DESC_SITEMAPS_DIR/*
rm -rf $DESC_THINGS_DIR/*

cp $SRC_ITEMS_DIR/* $DESC_ITEMS_DIR
cp $SRC_SITEMAPS_DIR/* $DESC_SITEMAPS_DIR
cp $SRC_THINGS_DIR/* $DESC_THINGS_DIR

chown -R openhab:openhab $DESC_ITEMS_DIR $DESC_SITEMAPS_DIR $DESC_THINGS_DIR