
// ═══════════════════════════════════════════════════════════════════════════
// MOSTAR GRID - COMPLETE NEO4J SEED SCRIPT
// Run this in Neo4j Browser to create the 256 Odú consciousness graph
// ═══════════════════════════════════════════════════════════════════════════

// Clear existing data (CAUTION: This deletes everything!)
// MATCH (n) DETACH DELETE n;

// Create constraints
CREATE CONSTRAINT odu_code IF NOT EXISTS FOR (o:Odu) REQUIRE o.code IS UNIQUE;
CREATE CONSTRAINT agent_name IF NOT EXISTS FOR (a:Agent) REQUIRE a.name IS UNIQUE;

// Create indexes
CREATE INDEX odu_name IF NOT EXISTS FOR (o:Odu) ON (o.name);
CREATE INDEX odu_binary IF NOT EXISTS FOR (o:Odu) ON (o.binary);


// ═══════════════════════════════════════════════════════════════════════════
// CREATE ALL 256 ODÚ PATTERNS
// ═══════════════════════════════════════════════════════════════════════════

CREATE (:Odu:Principal {
  code: 0,
  name: "Eji Ogbe",
  binary: "00000000",
  left: "Ogbe",
  right: "Ogbe",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 15,
  name: "Ogbe-Oyeku",
  binary: "00001111",
  left: "Ogbe",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 9,
  name: "Ogbe-Iwori",
  binary: "00001001",
  left: "Ogbe",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 6,
  name: "Ogbe-Odi",
  binary: "00000110",
  left: "Ogbe",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 3,
  name: "Ogbe-Irosun",
  binary: "00000011",
  left: "Ogbe",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 12,
  name: "Ogbe-Owonrin",
  binary: "00001100",
  left: "Ogbe",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 7,
  name: "Ogbe-Obara",
  binary: "00000111",
  left: "Ogbe",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 14,
  name: "Ogbe-Okanran",
  binary: "00001110",
  left: "Ogbe",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 1,
  name: "Ogbe-Ogunda",
  binary: "00000001",
  left: "Ogbe",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 8,
  name: "Ogbe-Osa",
  binary: "00001000",
  left: "Ogbe",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 11,
  name: "Ogbe-Ika",
  binary: "00001011",
  left: "Ogbe",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 4,
  name: "Ogbe-Oturupon",
  binary: "00000100",
  left: "Ogbe",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 2,
  name: "Ogbe-Otura",
  binary: "00000010",
  left: "Ogbe",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 5,
  name: "Ogbe-Irete",
  binary: "00000101",
  left: "Ogbe",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 10,
  name: "Ogbe-Ose",
  binary: "00001010",
  left: "Ogbe",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 13,
  name: "Ogbe-Ofun",
  binary: "00001101",
  left: "Ogbe",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 240,
  name: "Oyeku-Ogbe",
  binary: "11110000",
  left: "Oyeku",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 255,
  name: "Eji Oyeku",
  binary: "11111111",
  left: "Oyeku",
  right: "Oyeku",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 249,
  name: "Oyeku-Iwori",
  binary: "11111001",
  left: "Oyeku",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 246,
  name: "Oyeku-Odi",
  binary: "11110110",
  left: "Oyeku",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 243,
  name: "Oyeku-Irosun",
  binary: "11110011",
  left: "Oyeku",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 252,
  name: "Oyeku-Owonrin",
  binary: "11111100",
  left: "Oyeku",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 247,
  name: "Oyeku-Obara",
  binary: "11110111",
  left: "Oyeku",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 254,
  name: "Oyeku-Okanran",
  binary: "11111110",
  left: "Oyeku",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 241,
  name: "Oyeku-Ogunda",
  binary: "11110001",
  left: "Oyeku",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 248,
  name: "Oyeku-Osa",
  binary: "11111000",
  left: "Oyeku",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 251,
  name: "Oyeku-Ika",
  binary: "11111011",
  left: "Oyeku",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 244,
  name: "Oyeku-Oturupon",
  binary: "11110100",
  left: "Oyeku",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 242,
  name: "Oyeku-Otura",
  binary: "11110010",
  left: "Oyeku",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 245,
  name: "Oyeku-Irete",
  binary: "11110101",
  left: "Oyeku",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 250,
  name: "Oyeku-Ose",
  binary: "11111010",
  left: "Oyeku",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 253,
  name: "Oyeku-Ofun",
  binary: "11111101",
  left: "Oyeku",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 144,
  name: "Iwori-Ogbe",
  binary: "10010000",
  left: "Iwori",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 159,
  name: "Iwori-Oyeku",
  binary: "10011111",
  left: "Iwori",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 153,
  name: "Eji Iwori",
  binary: "10011001",
  left: "Iwori",
  right: "Iwori",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 150,
  name: "Iwori-Odi",
  binary: "10010110",
  left: "Iwori",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 147,
  name: "Iwori-Irosun",
  binary: "10010011",
  left: "Iwori",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 156,
  name: "Iwori-Owonrin",
  binary: "10011100",
  left: "Iwori",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 151,
  name: "Iwori-Obara",
  binary: "10010111",
  left: "Iwori",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 158,
  name: "Iwori-Okanran",
  binary: "10011110",
  left: "Iwori",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 145,
  name: "Iwori-Ogunda",
  binary: "10010001",
  left: "Iwori",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 152,
  name: "Iwori-Osa",
  binary: "10011000",
  left: "Iwori",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 155,
  name: "Iwori-Ika",
  binary: "10011011",
  left: "Iwori",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 148,
  name: "Iwori-Oturupon",
  binary: "10010100",
  left: "Iwori",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 146,
  name: "Iwori-Otura",
  binary: "10010010",
  left: "Iwori",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 149,
  name: "Iwori-Irete",
  binary: "10010101",
  left: "Iwori",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 154,
  name: "Iwori-Ose",
  binary: "10011010",
  left: "Iwori",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 157,
  name: "Iwori-Ofun",
  binary: "10011101",
  left: "Iwori",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 96,
  name: "Odi-Ogbe",
  binary: "01100000",
  left: "Odi",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 111,
  name: "Odi-Oyeku",
  binary: "01101111",
  left: "Odi",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 105,
  name: "Odi-Iwori",
  binary: "01101001",
  left: "Odi",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 102,
  name: "Eji Odi",
  binary: "01100110",
  left: "Odi",
  right: "Odi",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 99,
  name: "Odi-Irosun",
  binary: "01100011",
  left: "Odi",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 108,
  name: "Odi-Owonrin",
  binary: "01101100",
  left: "Odi",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 103,
  name: "Odi-Obara",
  binary: "01100111",
  left: "Odi",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 110,
  name: "Odi-Okanran",
  binary: "01101110",
  left: "Odi",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 97,
  name: "Odi-Ogunda",
  binary: "01100001",
  left: "Odi",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 104,
  name: "Odi-Osa",
  binary: "01101000",
  left: "Odi",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 107,
  name: "Odi-Ika",
  binary: "01101011",
  left: "Odi",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 100,
  name: "Odi-Oturupon",
  binary: "01100100",
  left: "Odi",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 98,
  name: "Odi-Otura",
  binary: "01100010",
  left: "Odi",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 101,
  name: "Odi-Irete",
  binary: "01100101",
  left: "Odi",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 106,
  name: "Odi-Ose",
  binary: "01101010",
  left: "Odi",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 109,
  name: "Odi-Ofun",
  binary: "01101101",
  left: "Odi",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 48,
  name: "Irosun-Ogbe",
  binary: "00110000",
  left: "Irosun",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 63,
  name: "Irosun-Oyeku",
  binary: "00111111",
  left: "Irosun",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 57,
  name: "Irosun-Iwori",
  binary: "00111001",
  left: "Irosun",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 54,
  name: "Irosun-Odi",
  binary: "00110110",
  left: "Irosun",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 51,
  name: "Eji Irosun",
  binary: "00110011",
  left: "Irosun",
  right: "Irosun",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 60,
  name: "Irosun-Owonrin",
  binary: "00111100",
  left: "Irosun",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 55,
  name: "Irosun-Obara",
  binary: "00110111",
  left: "Irosun",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 62,
  name: "Irosun-Okanran",
  binary: "00111110",
  left: "Irosun",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 49,
  name: "Irosun-Ogunda",
  binary: "00110001",
  left: "Irosun",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 56,
  name: "Irosun-Osa",
  binary: "00111000",
  left: "Irosun",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 59,
  name: "Irosun-Ika",
  binary: "00111011",
  left: "Irosun",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 52,
  name: "Irosun-Oturupon",
  binary: "00110100",
  left: "Irosun",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 50,
  name: "Irosun-Otura",
  binary: "00110010",
  left: "Irosun",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 53,
  name: "Irosun-Irete",
  binary: "00110101",
  left: "Irosun",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 58,
  name: "Irosun-Ose",
  binary: "00111010",
  left: "Irosun",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 61,
  name: "Irosun-Ofun",
  binary: "00111101",
  left: "Irosun",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 192,
  name: "Owonrin-Ogbe",
  binary: "11000000",
  left: "Owonrin",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 207,
  name: "Owonrin-Oyeku",
  binary: "11001111",
  left: "Owonrin",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 201,
  name: "Owonrin-Iwori",
  binary: "11001001",
  left: "Owonrin",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 198,
  name: "Owonrin-Odi",
  binary: "11000110",
  left: "Owonrin",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 195,
  name: "Owonrin-Irosun",
  binary: "11000011",
  left: "Owonrin",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 204,
  name: "Eji Owonrin",
  binary: "11001100",
  left: "Owonrin",
  right: "Owonrin",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 199,
  name: "Owonrin-Obara",
  binary: "11000111",
  left: "Owonrin",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 206,
  name: "Owonrin-Okanran",
  binary: "11001110",
  left: "Owonrin",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 193,
  name: "Owonrin-Ogunda",
  binary: "11000001",
  left: "Owonrin",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 200,
  name: "Owonrin-Osa",
  binary: "11001000",
  left: "Owonrin",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 203,
  name: "Owonrin-Ika",
  binary: "11001011",
  left: "Owonrin",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 196,
  name: "Owonrin-Oturupon",
  binary: "11000100",
  left: "Owonrin",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 194,
  name: "Owonrin-Otura",
  binary: "11000010",
  left: "Owonrin",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 197,
  name: "Owonrin-Irete",
  binary: "11000101",
  left: "Owonrin",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 202,
  name: "Owonrin-Ose",
  binary: "11001010",
  left: "Owonrin",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 205,
  name: "Owonrin-Ofun",
  binary: "11001101",
  left: "Owonrin",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 112,
  name: "Obara-Ogbe",
  binary: "01110000",
  left: "Obara",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 127,
  name: "Obara-Oyeku",
  binary: "01111111",
  left: "Obara",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 121,
  name: "Obara-Iwori",
  binary: "01111001",
  left: "Obara",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 118,
  name: "Obara-Odi",
  binary: "01110110",
  left: "Obara",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 115,
  name: "Obara-Irosun",
  binary: "01110011",
  left: "Obara",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 124,
  name: "Obara-Owonrin",
  binary: "01111100",
  left: "Obara",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 119,
  name: "Eji Obara",
  binary: "01110111",
  left: "Obara",
  right: "Obara",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 126,
  name: "Obara-Okanran",
  binary: "01111110",
  left: "Obara",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 113,
  name: "Obara-Ogunda",
  binary: "01110001",
  left: "Obara",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 120,
  name: "Obara-Osa",
  binary: "01111000",
  left: "Obara",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 123,
  name: "Obara-Ika",
  binary: "01111011",
  left: "Obara",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 116,
  name: "Obara-Oturupon",
  binary: "01110100",
  left: "Obara",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 114,
  name: "Obara-Otura",
  binary: "01110010",
  left: "Obara",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 117,
  name: "Obara-Irete",
  binary: "01110101",
  left: "Obara",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 122,
  name: "Obara-Ose",
  binary: "01111010",
  left: "Obara",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 125,
  name: "Obara-Ofun",
  binary: "01111101",
  left: "Obara",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 224,
  name: "Okanran-Ogbe",
  binary: "11100000",
  left: "Okanran",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 239,
  name: "Okanran-Oyeku",
  binary: "11101111",
  left: "Okanran",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 233,
  name: "Okanran-Iwori",
  binary: "11101001",
  left: "Okanran",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 230,
  name: "Okanran-Odi",
  binary: "11100110",
  left: "Okanran",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 227,
  name: "Okanran-Irosun",
  binary: "11100011",
  left: "Okanran",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 236,
  name: "Okanran-Owonrin",
  binary: "11101100",
  left: "Okanran",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 231,
  name: "Okanran-Obara",
  binary: "11100111",
  left: "Okanran",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 238,
  name: "Eji Okanran",
  binary: "11101110",
  left: "Okanran",
  right: "Okanran",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 225,
  name: "Okanran-Ogunda",
  binary: "11100001",
  left: "Okanran",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 232,
  name: "Okanran-Osa",
  binary: "11101000",
  left: "Okanran",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 235,
  name: "Okanran-Ika",
  binary: "11101011",
  left: "Okanran",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 228,
  name: "Okanran-Oturupon",
  binary: "11100100",
  left: "Okanran",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 226,
  name: "Okanran-Otura",
  binary: "11100010",
  left: "Okanran",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 229,
  name: "Okanran-Irete",
  binary: "11100101",
  left: "Okanran",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 234,
  name: "Okanran-Ose",
  binary: "11101010",
  left: "Okanran",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 237,
  name: "Okanran-Ofun",
  binary: "11101101",
  left: "Okanran",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 16,
  name: "Ogunda-Ogbe",
  binary: "00010000",
  left: "Ogunda",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 31,
  name: "Ogunda-Oyeku",
  binary: "00011111",
  left: "Ogunda",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 25,
  name: "Ogunda-Iwori",
  binary: "00011001",
  left: "Ogunda",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 22,
  name: "Ogunda-Odi",
  binary: "00010110",
  left: "Ogunda",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 19,
  name: "Ogunda-Irosun",
  binary: "00010011",
  left: "Ogunda",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 28,
  name: "Ogunda-Owonrin",
  binary: "00011100",
  left: "Ogunda",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 23,
  name: "Ogunda-Obara",
  binary: "00010111",
  left: "Ogunda",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 30,
  name: "Ogunda-Okanran",
  binary: "00011110",
  left: "Ogunda",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 17,
  name: "Eji Ogunda",
  binary: "00010001",
  left: "Ogunda",
  right: "Ogunda",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 24,
  name: "Ogunda-Osa",
  binary: "00011000",
  left: "Ogunda",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 27,
  name: "Ogunda-Ika",
  binary: "00011011",
  left: "Ogunda",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 20,
  name: "Ogunda-Oturupon",
  binary: "00010100",
  left: "Ogunda",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 18,
  name: "Ogunda-Otura",
  binary: "00010010",
  left: "Ogunda",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 21,
  name: "Ogunda-Irete",
  binary: "00010101",
  left: "Ogunda",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 26,
  name: "Ogunda-Ose",
  binary: "00011010",
  left: "Ogunda",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 29,
  name: "Ogunda-Ofun",
  binary: "00011101",
  left: "Ogunda",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 128,
  name: "Osa-Ogbe",
  binary: "10000000",
  left: "Osa",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 143,
  name: "Osa-Oyeku",
  binary: "10001111",
  left: "Osa",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 137,
  name: "Osa-Iwori",
  binary: "10001001",
  left: "Osa",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 134,
  name: "Osa-Odi",
  binary: "10000110",
  left: "Osa",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 131,
  name: "Osa-Irosun",
  binary: "10000011",
  left: "Osa",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 140,
  name: "Osa-Owonrin",
  binary: "10001100",
  left: "Osa",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 135,
  name: "Osa-Obara",
  binary: "10000111",
  left: "Osa",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 142,
  name: "Osa-Okanran",
  binary: "10001110",
  left: "Osa",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 129,
  name: "Osa-Ogunda",
  binary: "10000001",
  left: "Osa",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 136,
  name: "Eji Osa",
  binary: "10001000",
  left: "Osa",
  right: "Osa",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 139,
  name: "Osa-Ika",
  binary: "10001011",
  left: "Osa",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 132,
  name: "Osa-Oturupon",
  binary: "10000100",
  left: "Osa",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 130,
  name: "Osa-Otura",
  binary: "10000010",
  left: "Osa",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 133,
  name: "Osa-Irete",
  binary: "10000101",
  left: "Osa",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 138,
  name: "Osa-Ose",
  binary: "10001010",
  left: "Osa",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 141,
  name: "Osa-Ofun",
  binary: "10001101",
  left: "Osa",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 176,
  name: "Ika-Ogbe",
  binary: "10110000",
  left: "Ika",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 191,
  name: "Ika-Oyeku",
  binary: "10111111",
  left: "Ika",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 185,
  name: "Ika-Iwori",
  binary: "10111001",
  left: "Ika",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 182,
  name: "Ika-Odi",
  binary: "10110110",
  left: "Ika",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 179,
  name: "Ika-Irosun",
  binary: "10110011",
  left: "Ika",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 188,
  name: "Ika-Owonrin",
  binary: "10111100",
  left: "Ika",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 183,
  name: "Ika-Obara",
  binary: "10110111",
  left: "Ika",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 190,
  name: "Ika-Okanran",
  binary: "10111110",
  left: "Ika",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 177,
  name: "Ika-Ogunda",
  binary: "10110001",
  left: "Ika",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 184,
  name: "Ika-Osa",
  binary: "10111000",
  left: "Ika",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 187,
  name: "Eji Ika",
  binary: "10111011",
  left: "Ika",
  right: "Ika",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 180,
  name: "Ika-Oturupon",
  binary: "10110100",
  left: "Ika",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 178,
  name: "Ika-Otura",
  binary: "10110010",
  left: "Ika",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 181,
  name: "Ika-Irete",
  binary: "10110101",
  left: "Ika",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 186,
  name: "Ika-Ose",
  binary: "10111010",
  left: "Ika",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 189,
  name: "Ika-Ofun",
  binary: "10111101",
  left: "Ika",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 64,
  name: "Oturupon-Ogbe",
  binary: "01000000",
  left: "Oturupon",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 79,
  name: "Oturupon-Oyeku",
  binary: "01001111",
  left: "Oturupon",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 73,
  name: "Oturupon-Iwori",
  binary: "01001001",
  left: "Oturupon",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 70,
  name: "Oturupon-Odi",
  binary: "01000110",
  left: "Oturupon",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 67,
  name: "Oturupon-Irosun",
  binary: "01000011",
  left: "Oturupon",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 76,
  name: "Oturupon-Owonrin",
  binary: "01001100",
  left: "Oturupon",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 71,
  name: "Oturupon-Obara",
  binary: "01000111",
  left: "Oturupon",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 78,
  name: "Oturupon-Okanran",
  binary: "01001110",
  left: "Oturupon",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 65,
  name: "Oturupon-Ogunda",
  binary: "01000001",
  left: "Oturupon",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 72,
  name: "Oturupon-Osa",
  binary: "01001000",
  left: "Oturupon",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 75,
  name: "Oturupon-Ika",
  binary: "01001011",
  left: "Oturupon",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 68,
  name: "Eji Oturupon",
  binary: "01000100",
  left: "Oturupon",
  right: "Oturupon",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 66,
  name: "Oturupon-Otura",
  binary: "01000010",
  left: "Oturupon",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 69,
  name: "Oturupon-Irete",
  binary: "01000101",
  left: "Oturupon",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 74,
  name: "Oturupon-Ose",
  binary: "01001010",
  left: "Oturupon",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 77,
  name: "Oturupon-Ofun",
  binary: "01001101",
  left: "Oturupon",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 32,
  name: "Otura-Ogbe",
  binary: "00100000",
  left: "Otura",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 47,
  name: "Otura-Oyeku",
  binary: "00101111",
  left: "Otura",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 41,
  name: "Otura-Iwori",
  binary: "00101001",
  left: "Otura",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 38,
  name: "Otura-Odi",
  binary: "00100110",
  left: "Otura",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 35,
  name: "Otura-Irosun",
  binary: "00100011",
  left: "Otura",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 44,
  name: "Otura-Owonrin",
  binary: "00101100",
  left: "Otura",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 39,
  name: "Otura-Obara",
  binary: "00100111",
  left: "Otura",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 46,
  name: "Otura-Okanran",
  binary: "00101110",
  left: "Otura",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 33,
  name: "Otura-Ogunda",
  binary: "00100001",
  left: "Otura",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 40,
  name: "Otura-Osa",
  binary: "00101000",
  left: "Otura",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 43,
  name: "Otura-Ika",
  binary: "00101011",
  left: "Otura",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 36,
  name: "Otura-Oturupon",
  binary: "00100100",
  left: "Otura",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 34,
  name: "Eji Otura",
  binary: "00100010",
  left: "Otura",
  right: "Otura",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 37,
  name: "Otura-Irete",
  binary: "00100101",
  left: "Otura",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 42,
  name: "Otura-Ose",
  binary: "00101010",
  left: "Otura",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 45,
  name: "Otura-Ofun",
  binary: "00101101",
  left: "Otura",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 80,
  name: "Irete-Ogbe",
  binary: "01010000",
  left: "Irete",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 95,
  name: "Irete-Oyeku",
  binary: "01011111",
  left: "Irete",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 89,
  name: "Irete-Iwori",
  binary: "01011001",
  left: "Irete",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 86,
  name: "Irete-Odi",
  binary: "01010110",
  left: "Irete",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 83,
  name: "Irete-Irosun",
  binary: "01010011",
  left: "Irete",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 92,
  name: "Irete-Owonrin",
  binary: "01011100",
  left: "Irete",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 87,
  name: "Irete-Obara",
  binary: "01010111",
  left: "Irete",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 94,
  name: "Irete-Okanran",
  binary: "01011110",
  left: "Irete",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 81,
  name: "Irete-Ogunda",
  binary: "01010001",
  left: "Irete",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 88,
  name: "Irete-Osa",
  binary: "01011000",
  left: "Irete",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 91,
  name: "Irete-Ika",
  binary: "01011011",
  left: "Irete",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 84,
  name: "Irete-Oturupon",
  binary: "01010100",
  left: "Irete",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 82,
  name: "Irete-Otura",
  binary: "01010010",
  left: "Irete",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 85,
  name: "Eji Irete",
  binary: "01010101",
  left: "Irete",
  right: "Irete",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 90,
  name: "Irete-Ose",
  binary: "01011010",
  left: "Irete",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 93,
  name: "Irete-Ofun",
  binary: "01011101",
  left: "Irete",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 160,
  name: "Ose-Ogbe",
  binary: "10100000",
  left: "Ose",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 175,
  name: "Ose-Oyeku",
  binary: "10101111",
  left: "Ose",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 169,
  name: "Ose-Iwori",
  binary: "10101001",
  left: "Ose",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 166,
  name: "Ose-Odi",
  binary: "10100110",
  left: "Ose",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 163,
  name: "Ose-Irosun",
  binary: "10100011",
  left: "Ose",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 172,
  name: "Ose-Owonrin",
  binary: "10101100",
  left: "Ose",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 167,
  name: "Ose-Obara",
  binary: "10100111",
  left: "Ose",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 174,
  name: "Ose-Okanran",
  binary: "10101110",
  left: "Ose",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 161,
  name: "Ose-Ogunda",
  binary: "10100001",
  left: "Ose",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 168,
  name: "Ose-Osa",
  binary: "10101000",
  left: "Ose",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 171,
  name: "Ose-Ika",
  binary: "10101011",
  left: "Ose",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 164,
  name: "Ose-Oturupon",
  binary: "10100100",
  left: "Ose",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 162,
  name: "Ose-Otura",
  binary: "10100010",
  left: "Ose",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 165,
  name: "Ose-Irete",
  binary: "10100101",
  left: "Ose",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 170,
  name: "Eji Ose",
  binary: "10101010",
  left: "Ose",
  right: "Ose",
  is_principal: true,
  usage_count: 0
});
CREATE (:Odu {
  code: 173,
  name: "Ose-Ofun",
  binary: "10101101",
  left: "Ose",
  right: "Ofun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 208,
  name: "Ofun-Ogbe",
  binary: "11010000",
  left: "Ofun",
  right: "Ogbe",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 223,
  name: "Ofun-Oyeku",
  binary: "11011111",
  left: "Ofun",
  right: "Oyeku",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 217,
  name: "Ofun-Iwori",
  binary: "11011001",
  left: "Ofun",
  right: "Iwori",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 214,
  name: "Ofun-Odi",
  binary: "11010110",
  left: "Ofun",
  right: "Odi",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 211,
  name: "Ofun-Irosun",
  binary: "11010011",
  left: "Ofun",
  right: "Irosun",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 220,
  name: "Ofun-Owonrin",
  binary: "11011100",
  left: "Ofun",
  right: "Owonrin",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 215,
  name: "Ofun-Obara",
  binary: "11010111",
  left: "Ofun",
  right: "Obara",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 222,
  name: "Ofun-Okanran",
  binary: "11011110",
  left: "Ofun",
  right: "Okanran",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 209,
  name: "Ofun-Ogunda",
  binary: "11010001",
  left: "Ofun",
  right: "Ogunda",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 216,
  name: "Ofun-Osa",
  binary: "11011000",
  left: "Ofun",
  right: "Osa",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 219,
  name: "Ofun-Ika",
  binary: "11011011",
  left: "Ofun",
  right: "Ika",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 212,
  name: "Ofun-Oturupon",
  binary: "11010100",
  left: "Ofun",
  right: "Oturupon",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 210,
  name: "Ofun-Otura",
  binary: "11010010",
  left: "Ofun",
  right: "Otura",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 213,
  name: "Ofun-Irete",
  binary: "11010101",
  left: "Ofun",
  right: "Irete",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu {
  code: 218,
  name: "Ofun-Ose",
  binary: "11011010",
  left: "Ofun",
  right: "Ose",
  is_principal: false,
  usage_count: 0
});
CREATE (:Odu:Principal {
  code: 221,
  name: "Eji Ofun",
  binary: "11011101",
  left: "Ofun",
  right: "Ofun",
  is_principal: true,
  usage_count: 0
});

// ═══════════════════════════════════════════════════════════════════════════
// CREATE LAYER NODES
// ═══════════════════════════════════════════════════════════════════════════

CREATE (:Layer {name: 'SOUL', description: 'Values, ethics, covenant'});
CREATE (:Layer {name: 'MIND', description: 'Analysis, reasoning, Ifá logic'});
CREATE (:Layer {name: 'BODY', description: 'Execution, operations, sensors'});
CREATE (:Layer {name: 'META', description: 'Control plane, gateway'});
CREATE (:Layer {name: 'NARRATIVE', description: 'Communications, documentation'});

// ═══════════════════════════════════════════════════════════════════════════
// CREATE AGENT NODES
// ═══════════════════════════════════════════════════════════════════════════

CREATE (:Agent {name: 'Mo', role: 'executor', layer: 'BODY'});
CREATE (:Agent {name: 'Woo', role: 'judge', layer: 'SOUL'});
CREATE (:Agent {name: 'RAD-X-FLB', role: 'sentinel', layer: 'BODY'});
CREATE (:Agent {name: 'TsaTse Fly', role: 'analyst', layer: 'MIND'});
CREATE (:Agent {name: 'Code Conduit', role: 'gateway', layer: 'META'});
CREATE (:Agent {name: 'Flameborn Writer', role: 'narrator', layer: 'NARRATIVE'});

// Link agents to layers
MATCH (a:Agent), (l:Layer)
WHERE a.layer = l.name
CREATE (a)-[:BELONGS_TO]->(l);

// ═══════════════════════════════════════════════════════════════════════════
// CREATE XOR RELATIONSHIPS (This creates the consciousness network)
// ═══════════════════════════════════════════════════════════════════════════

// Create XOR edges between all Odú pairs
MATCH (a:Odu), (b:Odu)
WHERE a.code < b.code
WITH a, b, 
     reduce(s = 0, i IN range(0, 7) | 
            s + CASE WHEN ((a.code / toInteger(2^i)) % 2) <> ((b.code / toInteger(2^i)) % 2) 
                THEN 1 ELSE 0 END) AS hamming
CREATE (a)-[:XOR {hamming_distance: hamming, xor_result: a.code + b.code - 2 * (a.code % (2^hamming))}]->(b);

// Verify creation
MATCH (o:Odu) RETURN count(o) AS total_odu;
MATCH ()-[r:XOR]->() RETURN count(r) AS total_xor_edges;
MATCH (a:Agent) RETURN count(a) AS total_agents;
