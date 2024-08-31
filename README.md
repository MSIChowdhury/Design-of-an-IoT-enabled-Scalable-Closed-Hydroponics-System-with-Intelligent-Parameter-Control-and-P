# Design of an IoT-enabled Scalable Closed Hydroponics System with Intelligent Parameter Control and Persistent Sensing Error Resilience

## Overview

This repository contains the implementation of an IoT-enabled scalable closed hydroponics system with intelligent parameter control and persistent sensing error resilience. The project aims to address the challenges posed by climate change and global warming to traditional agriculture by developing an advanced automated hydroponics solution.

## Authors

- MD. Sameer Iqbal Chowdhury - Department of Robotics and Mechatronics Engineering, University of Dhaka, Bangladesh
- Mikdam-Al-Maad Ronoue - Department of Robotics and Mechatronics Engineering, University of Dhaka, Bangladesh

## Supervisors

- Dr. Lafifa Jamal - Department of Robotics and Mechatronics Engineering, University of Dhaka, Bangladesh
- Dr. Md Asaduzzaman - Department of Agriculture and Food Technology, Kyoto University of Advanced Sciences

## Features

1. Automated monitoring and control of key physical parameters for optimal plant growth
2. Web-based dashboard for displaying sensor data
3. Intelligent control action classifier using machine learning
4. Persistent error resilience algorithm for improved sensor data accuracy

## System Components

- IoT-enabled sensors and actuators
- Web-based dashboard
- Machine learning models for intelligent control
- Error resilience algorithm

## Experiments and Results

1. Two experimental iterations under different weather conditions
2. Comparison of the system against soil-based and manual Deep Water Culture (DWC) methods
3. Significantly higher fresh mass yield compared to traditional methods
4. Successful implementation of the error resilience algorithm, reducing erroneous sensor data instances

## Machine Learning Models

- Multiple models trained and tested
- XGBoostClassifier achieved the best performance:
  - Accuracy: 0.98
  - Recall: 0.97
  - Precision: 0.96
  - F1-score: 0.96

## Error Resilience Algorithm

- Developed as a constrained optimization problem
- Utilizes a cost function and adaptive multi-parameter λ-weighted minimization approach
- Implemented update policies for improved performance
- Resulted in ~4 times reduction in instances of erroneous sensor data

## Acknowledgements

We gratefully acknowledge the financial support provided
by the ICT Division under the Ministry of Communications
and Information Technology, People's Republic of Bangladesh. This research was fully funded
under the ICT Innovation Fund arranged by the ICT Division.
