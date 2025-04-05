# from crewai.tools import BaseTool
# from pydantic import BaseModel, Field
# from typing import List, Dict, Optional, Type
# import os
# import requests
# import csv
# import re
# from tqdm import tqdm
# from itertools import product
# from dotenv import load_dotenv

# # Load access token securely from .env
# load_dotenv()
# ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

# class FacebookAdScraperInput(BaseModel):
#     """Input schema for Facebook Ad Scraper Tool."""
#     search_terms: Optional[str] = Field(None, description="Search terms for Facebook ads.")
#     ad_active_status: str = Field(..., description="Active status of the ad (e.g., 'ALL', 'ACTIVE').")
#     search_page_ids: Optional[List[str]] = Field([], description="List of page IDs to filter the search.")
#     regions: List[str] = Field(..., description="List of regions to filter the ad data.")
#     demo_ages: List[str] = Field(..., description="List of demographic ages to filter the ads.")
#     demo_genders: List[str] = Field(..., description="List of demographic genders to filter the ads.")
#     query_fields: List[str] = Field(..., description="List of fields to retrieve from the ads.")
#     page_total: int = Field(10, description="Number of ads to fetch per page.")
#     search_total: int = Field(100, description="Total number of ads to fetch.")


# class FacebookAdScraperTool(BaseTool):
#     name: str = "facebook_ad_scraper"
#     description: str = "Scrapes Facebook Ad Library data using Facebook Graph API."
#     args_schema: Type[BaseModel] = FacebookAdScraperInput

#     def _run(
#         self,
#         search_terms: Optional[str],
#         ad_active_status: str,
#         search_page_ids: Optional[List[str]],
#         regions: List[str],
#         demo_ages: List[str],
#         demo_genders: List[str],
#         query_fields: List[str],
#         page_total: int = 10,
#         search_total: int = 100
#     ) -> Dict[str, List[Dict[str, Optional[str]]]]:

#         try:
#             if not ACCESS_TOKEN:
#                 raise Exception("Facebook access token not set. Please define FB_ACCESS_TOKEN in your .env file.")

#             base_url = "https://graph.facebook.com/v18.0/ads_archive"

#             params = {
#                 "access_token": ACCESS_TOKEN,
#                 "ad_type": "POLITICAL_AND_ISSUE_ADS",
#                 "ad_active_status": ad_active_status,
#                 "ad_reached_countries": "GB",
#                 "search_terms": search_terms,
#                 "search_page_ids": ",".join(search_page_ids) if search_page_ids else "",
#                 "fields": ",".join(query_fields),
#                 "limit": page_total
#             }

#             REGIONS = set(regions)
#             DEMOS = set(product(demo_ages, demo_genders))

#             with open("fb_ads.csv", "w", newline='', encoding='utf-8') as f1, \
#                  open("fb_ads_demos.csv", "w", newline='', encoding='utf-8') as f2, \
#                  open("fb_ads_regions.csv", "w", newline='', encoding='utf-8') as f3:

#                 w1 = csv.DictWriter(f1, fieldnames=query_fields + ['ad_id', 'ad_url', 'impressions_min', 'impressions_max', 'spend_min', 'spend_max'], extrasaction='ignore')
#                 w1.writeheader()

#                 w2 = csv.DictWriter(f2, fieldnames=['ad_id', 'age', 'gender', 'percentage'], extrasaction='ignore')
#                 w2.writeheader()

#                 w3 = csv.DictWriter(f3, fieldnames=['ad_id', 'region', 'percentage'], extrasaction='ignore')
#                 w3.writeheader()

#                 ads_collected = 0
#                 pbar = tqdm(total=search_total, smoothing=0)

#                 while ads_collected < search_total:
#                     response = requests.get(base_url, params=params)
#                     data = response.json()

#                     if "error" in data:
#                         raise Exception(data["error"]["message"])

#                     for ad in data.get("data", []):
#                         if 'ad_snapshot_url' not in ad:
#                             continue

#                         ad_id_match = re.search(r'\d+', ad["ad_snapshot_url"])
#                         if not ad_id_match:
#                             continue
#                         ad_id = ad_id_match.group(0)
#                         ad_url = f"https://www.facebook.com/ads/library/?id={ad_id}"

#                         demo_set = set()
#                         for demo in ad.get("demographic_distribution", []):
#                             demo.update({'ad_id': ad_id})
#                             w2.writerow(demo)
#                             demo_set.add((demo['age'], demo['gender']))

#                         for demo in DEMOS - demo_set:
#                             w2.writerow({
#                                 'ad_id': ad_id,
#                                 'age': demo[0],
#                                 'gender': demo[1],
#                                 'percentage': 0
#                             })

#                         region_set = set()
#                         for region in ad.get("region_distribution", []):
#                             region.update({'ad_id': ad_id})
#                             w3.writerow(region)
#                             region_set.add(region["region"])

#                         for region in REGIONS - region_set:
#                             w3.writerow({
#                                 'ad_id': ad_id,
#                                 'region': region,
#                                 'percentage': 0
#                             })

#                         ad.update({
#                             'ad_id': ad_id,
#                             'ad_url': ad_url,
#                             'impressions_min': ad.get('impressions', {}).get('lower_bound'),
#                             'impressions_max': ad.get('impressions', {}).get('upper_bound'),
#                             'spend_min': ad.get('spend', {}).get('lower_bound'),
#                             'spend_max': ad.get('spend', {}).get('upper_bound')
#                         })

#                         w1.writerow(ad)
#                         ads_collected += 1
#                         pbar.update(1)

#                         if ads_collected >= search_total:
#                             break

#                     if "paging" not in data or "next" not in data["paging"]:
#                         break

#                     next_url = data["paging"]["next"]
#                     params = {}  # Clear params for the next full URL call
#                     base_url = next_url

#                 pbar.close()

#             return {
#                 "summary": {
#                     "query": search_terms,
#                     "total_results": search_total,
#                     "ads_collected": ads_collected
#                 },
#                 "status": "Completed"
#             }

#         except Exception as e:
#             return {"error": f"Error scraping Facebook Ad Library: {str(e)}"}
