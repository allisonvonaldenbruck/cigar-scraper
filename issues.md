# Issues

## Open
 14. add code to track promotions (ex upgrade or free with sale) maybe col in data?
 31. update documentation/comments
 36. build test cases, download some HTML pages to use for tests
 41. handle unmatched cigars
 44. command line args to run in specific modes
 45. move to aws for data storage and running on schedule
 46. collect review data as data point on sales numbers
 47. collect stock data as available as data point on sales numbers
 48. collect google analytics data as data point on sales numbers
 49. use collected data to estimate sales numbers of https://www.neptunecigar.com/cigars/1502-black-gold-robusto
 50. collect and compare data of https://www.neptunecigar.com/cigars/1502-black-gold-robusto
 52. Do join in python code (see queries make_join_table)
 55. only add new price data if price changed from last recorded price
 56. send data to S3 bucket
 61. figure out why the number of rows in the equivalent_sku table is inconsistent after running, dropping table, then just running clean data func (went from 5 to 8 in the debug db) 
 63. scrape review data
 64. handle timeouts if one site is not responding
 65. manually create neptune dbs
 66. match neptune data


## Closed
 1. Scrape data from https://www.cigarsinternational.com/shop/big-list-of-cigars-brands/1803000/
 2. pull data from zip into database
 3. generate table matching skus from one site to other site
 4. generate table that compares cigar prices of same item on different sites
 5. pre-generate table with primary keys, index, etc.
 6. improve error checking in `write_to_db()`. check for duplicate data, if table exists, etc.
 7. setup foreign key relationships in `equivalent_id_data` table
 9. scrape stick size data from international site
 10. handle different quantity of sticks being matched as same product
 11. remove ’ (it's not a ' or a \` in the db and `strip('’')` doesn't work)
 12. fix scraping, it's missing a lot of data
 16. clean up size better so they both follow the same format 1.0x55, handle smoke inn rounding sizes vs inter not rounding sizes
 17. filter out data that has no match
 19. make join table for matching items
 21. re-work how scraping works
 22. rework data collation for new dataset
 23. lookup list of cigar shapes to filter for
 24. scrape smoke inn data for cleaner data set
 27. speed up smoke inn scraping, probably need to do each brand in a separate thread
 26. refactor code into separate modules for readability
 29. clean new smoke inn data, attempt to match it with inter data
 30. clean up db and funcs, remove things like *_2
 32. fix depreciation errors from calling df[col].str.replace()
 33. fix inter size data so it matches smoke inn format in all cases
 34. find stick types for smoke_inn data
 35. try matching data again
 37. fix cleaning data for qty, some still come back with # ct in smoke inn data
 38. separate out sub-brands of brands via product manufacturer
 39. double check manufacturers on inter data
 40. Implement process outlined below
 42. Collect price data over time
 43. cleanup unused code
 51. create table before inserting data in queries to ensure correct data structure
 53. debug log file
 54. fix bug with db throwing error if db already exists
 57. use proxy service for scraping
 58. create aws resources via terraform rwf: https://www.youtube.com/watch?v=nvNqfgojocs&list
     1. move from sqlite to mysql for db connection 
     2. pull code and dependencies from git when created, then run on set schedule
     3. move secrets to own dir
     4. move db login info into file so it doesn't need to be hard coded
     5. test db connection on aws instance (probably need to add port)
 59. fix issue where doesn't always run scrape 
 60. fix issue where international data is missing half the rows
 62. Scrape Neptunecigars.com

## Abandon
 8. fix stick name table headers
 13. Add filter for products that are no longer available, see https://www.cigarsinternational.com/p/aging-room-quattro-connecticut/2016290/ for an example (currently unneeded)
 15. fix prices bug in data scraping func - can't find/already fixed
 18. match data via fuzzy search (unneeded now)
 20. Add check to remove null row from smoke inn data import (moot with switch to scraped data)
 25. work in manufacturer data to scraper, as well as stick data, from big lists on site (done/unneeded now)
 28. improve insert to sql functions to check for dupe data (dup data should be overwritten with new timestamp)

## Notes

send over matched data 

get public endpoint for cigar data db
start pulling reviews


collect price data for all cigars, not just matching ones


issues with remote server not seeing newest versions of pandas, numpy, etc.

current goal:
terraform creates setup for code to live in
needs:
 1. ec2 server to run on
 2. get scrapingBee api key onto bucket somehow
 3. rds instance to store data
 4. connect rds to ec2 instance
 6. internet access (default ec2 instance has this)
 7. teardown ec2 server after code is run, but not s3 bucket
 8. s3 bucket for log to live in
 9. same conditions as db ec2 bucket
 10. rdb needs to be exposed so data can be accessed via powerBI
 11. probably need an AWS secrets Manager
 12. need a non-root user to do all this on

process: (ex ref https://medium.com/strategio/using-terraform-to-create-aws-vpc-ec2-and-rds-instances-c7f3aa416133)
 1. create vpc for everything to live in
 2. create rds instance for database
 3. create s3 instance for log file (maybe only do this on errors)
 4. lambda function to create ec2 instance that dose the following
    1.  create instance
    2.  connect ec2 to log bucket and db
    3.  pull crawler from git
    4.  install pre-requs
    5.  get scraping bee credentials
    6.  get git credentials
    7.  run crawler
    8.  tear down crawler
    9.  may need to add ssh credentials as well, not sure yet
 5. run the lambda func once/day 
 6. ideally set this all up via terraform to be easier to export



`cp data/cigarData.db /media/ian/extra`


deployment/hosting:
lives on AWS cloud
db stored in cloud
runs 1/day via cron job
pull updates from git main
only push to git main if passes tests
otherwise use dev branch for untested issue merges
day -> week -> month backup for db

able to cross-reference data
historic price data
eyeball check more data
handle lighter data

track sales data, qty data, historic data

Power BI frontend
AWS backend (magento as well)
aws structure, smoke inn under vonarosa but separate account?
security for private data


can I find sales volume here: https://www.neptunecigar.com/cigars/1502-black-gold-robusto
compare qty of reviews maybe
google analytics traffic for site
get smoke inn data for comparison


some bad matches in data:
ex SKU32894, HEM-PM-1002
should match to https://www.smoke_inn.com/Drew-Estate-Herrera-Esteli-Brazilian-Maduro/,
not https://www.smoke_inn.com/Drew-Estate-Factory-Smokes-Maduro-Toro.html

webbi/powerBi based dashboard


SKUs that should match but may be difficult:
Inter, Smoke inn
YOB-PM-1003,sku155921
3T3-PM-1006,sku24149
1OB-PM-1017,sku15011
6BC-PM-1031,sku504381
6BC-PM-1014,sku50298 (probably)