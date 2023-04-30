# iNeuronFlaskChallenge

## Environments and Usage
- Conda Environment: flaskDemo
    conda activate flaskDemo
- Conda Python Exe: /opt/anaconda3/envs/flaskDemo/bin/python
- Conda Python Ver: 3.10
- Conda Installations: 
    conda install -c conda-forge flask-pymongo

- Generating requirements.txt
    conda list -e
    python -m  pipreqs.pipreqs --force .

- AWS Pipeline
    - Create Elastic BeanStalk Environment
    - Create Code Pipeline