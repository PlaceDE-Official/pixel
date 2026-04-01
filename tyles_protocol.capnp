@0xb9d1af4e7e20c26e;

struct CanvasConfig @0xd544cf459a5618fc {
  sizeX @0 :UInt16;
  sizeY @1 :UInt16;
  colors @2 :List(Text);
  colorMap @3 :List(UInt8);
}

struct TileUpdate @0xed6c94507f98d4ef {
  x @0 :UInt16;
  y @1 :UInt16;
  color @2 :UInt8;
}

struct CanvasUpdate @0x944c20a7a98b2212 {
  currentTimestamp @0 :UInt32;
  previousTimestamp @1 :UInt32;
  union {
    config @2 :CanvasConfig;
    pixelUpdates @3 :List(TileUpdate);
  }
}
