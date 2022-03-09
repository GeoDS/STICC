[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://geods.geography.wisc.edu/">
    <img src="images/GeoDSLogo.jpg" alt="Logo" width="400">

  <h2 align="center">STICC: A multivariate spatial clustering method for repeated geographic pattern discovery with consideration of spatial contiguity</h2>

  <p align="center">
    GeoDS Lab, Department of Geography, University of Wisconsin-Madison.
    <br />
  </p>
</p>

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [Citation](#citation)
* [About the Project](#about-the-project)
* [Code Usage](#code-usage)
* [Folder Structure](#folder-structure)
* [License](#license)
* [Contact](#contact)
* [Acknowledgements](#acknowledgements)

<!-- Citation -->
## Citation
If you use this dataset in your research or applications, please cite this source:

Kang, Y., Wu, K., Gao, S., Ng, I., Rao, J., Ye, S., Zhang, F. and Fei, T. STICC: A multivariate spatial clustering method for repeated geographic pattern discovery with consideration of spatial contiguity. *International Journal of Geographical Information Science* (2022).
    

```
@article{kang2022sticc,
  title     = {STICC: A multivariate spatial clustering method for repeated geographic pattern discovery with consideration of spatial contiguity},
  author    = {Kang, Yuhao and Wu, Kunlin and Gao, Song and Ng, Ignavier and Rao, Jinmeng and Ye, Shan and Zhang, Fan and Fei, Teng},
  journal   = {International Journal of Geographical Information Science},
  year = {2022}
}
```

<!-- ABOUT THE PROJECT -->
## About The Project
Spatial clustering has been widely used for spatial data mining and knowledge discovery. An ideal multivariate spatial clustering should consider both spatial contiguity and aspatial attributes. Existing spatial clustering approaches may face challenges for discovering repeated geographic patterns with spatial contiguity maintained. In this paper, we propose a Spatial Toeplitz Inverse Covariance-Based Clustering (STICC) method that considers both attributes and spatial relationships of geographic objects for multivariate spatial clustering. A subregion is created for each geographic object serving as the basic unit when performing clustering. A Markov random Field (MRF) is then constructed to characterize the attribute dependencies of subregions. Using a spatial consistency strategy, nearby objects are encouraged to belong to the same cluster. To test the performance of the proposed STICC algorithm, we apply it in two use cases. The comparison results with several baseline methods show that the STICC outperforms others significantly in terms of adjusted rand index and macro-F1. Joint count statistics is also calculated and shows that the spatial contiguity is well preserved by STICC. Such a spatial clustering method may benefit various applications in the fields of geography, remote sensing, transportation, and urban planning, etc.

## Code Usage


## Folder Structure 
The folders and files are organized as follows.   
```
project
|-- codes
|-- daily_flows
|   |-- state2state
|   |   |-- daily_state2state_2020_03_01.csv
|   |   |-- daily_state2state_2020_03_02.csv
|   |   `-- ...
|   |-- county2county
|       |-- 2020_03_02
|       |   |-- weekly_ct2ct_2020_03_02_01.csv
|       |   |-- weekly_ct2ct_2020_03_02_02.csv
|       |   `-- ...
|       |-- 2020_03_09
|       |   |-- weekly_ct2ct_2020_03_09_01.csv
|       |   |-- weekly_ct2ct_2020_03_09_02.csv
|       |   `-- ...
|       `-- ...
`-- weekly_country_flows
```

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<!-- CONTACT -->
## Contact

Yuhao Kang - [@YuhaoKang](https://twitter.com/YuhaoKang) - yuhao.kang at wisc.edu  
Song Gao - [@gissong](https://twitter.com/gissong) - song.gao at wisc.edu  

Project Link: [https://github.com/GeoDS/STICC](https://github.com/GeoDS/STICC)  

<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
We would like to thank the funding support provided by the National Science Foundation (Award No. BCS-2027375). Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation. Support for this research was partly provided by the University of Wisconsin - Madison Office of the Vice Chancellor for Research and Graduate Education with funding from the Wisconsin Alumni Research Foundation.

<!-- MARKDOWN LINKS & IMAGES -->
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=flat-square
[license-url]: https://github.com/GeoDS/COVID19USFlows/blob/master/LICENSE.txt
