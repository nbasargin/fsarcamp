"""
Constant definitions for the HTERRA 2022 F-SAR campaign.

Time periods: 8 flights and 8 intensive ground measurement periods
Image areas: 8 areas with intensive ground measurements (specific fields)
"""

# Time periods

APR_28_AM = "APR-28-AM" # Flight 1, April 28 morning
APR_28_PM = "APR-28-PM" # Flight 2, April 28 afternoon
APR_29_AM = "APR-29-AM" # Flight 3, April 29 morning
APR_29_PM = "APR-29-PM" # Flight 4, April 29 afternoon
JUN_15_AM = "JUN-15-AM" # Flight 5, June 15 morning
JUN_15_PM = "JUN-15-PM" # Flight 6, June 15 afternoon
JUN_16_AM = "JUN-16-AM" # Flight 7, June 16 morning
JUN_16_PM = "JUN-16-PM" # Flight 8, June 16 afternoon

# Image areas / fields

CREA = "CREA" # all fields on the CREA farm, covers both April and June
APR_CREA_BS = "APR-CREA-BS" # Bare soil field at the CREA farm in April (same field as JUN-CREA-QU)
APR_CREA_DW = "APR-CREA-DW" # Durum wheat field at the CREA farm in Apri
JUN_CREA_SF = "JUN-CREA-SF" # Sunflower field at the CREA farm in June
JUN_CREA_QU = "JUN-CREA-QU" # Quinoa field at the CREA farm in June (same field as APR-CREA-BS)
JUN_CREA_MA = "JUN-CREA-MA" # Maize (corn) field at the CREA farm in June
CAIONE = "CAIONE" # all fields on the Caione farm, covers both April and June
APR_CAIONE_DW = "APR-CAIONE-DW" # Two adjacent durum wheat fields at the Caione farm in April
JUN_CAIONE_AA = "JUN-CAIONE-AA" # Alfalfa field at the Caione farm in June
JUN_CAIONE_MA = "JUN-CAIONE-MA" # Two adjacent maize (corn) fields at the Caione farm in June
