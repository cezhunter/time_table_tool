### Instructions

update config file `src/data/hs_conf` with your info

`pip install .` to install

`hs_util` to run

should be useful for a cron job :)

#### Commands

`hs_util table --help`

`hs_util table -test`

`hs_util table -date 23-10-2022`

##### todo

* write unit tests
* add comprehensive documentation
* implement auth caching
* handle api rate limitations
* general optimizations
    - data frame populating
    - concurrent api calls
