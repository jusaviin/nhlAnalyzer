# Classes to define PyTorch-based neural networks

import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class PlayerDataset(Dataset):
    """
    Class that handles data feeding to PyTorch-based naural network model
    Inherits from the PyTorch Dataset class
    """
    
    def __init__(self, features, salary):
        """
        Class constructor. Initializes the features to predict the salary and salary itself.
        
        Arguments:
            features = Features in form of numpy.ndarray
            salary = Salary in form of numpy.ndarray
        """
        self.features = torch.from_numpy(features.astype(np.float32, copy=False))
        self.salary = torch.from_numpy(salary.astype(np.float32, copy=True)).unsqueeze(1)
        
    def __getitem__(self,index):
        """
        Implement indexing for the PlayerDataset
        """
        return self.features[index], self.salary[index]
        
    def __len__(self):
        """
        Define length for the PlayerDataset
        """
        return len(self.features)


class PlayerNetwork(nn.Module):
    """
    Class defining the neural network structure for predicting player salaries.
    Inherits from Module in PyTorch
    """

    def __init__(self,input_dimension,hidden1,hidden2):
        """
        Initilization of network.
        """
        super(PlayerNetwork,self).__init__()
        self.linear1=nn.Linear(input_dimension,hidden1)
        self.relu1 = nn.ReLU()
        self.linear2=nn.Linear(hidden1,hidden2)
        self.relu2 = nn.ReLU()
        self.linear3=nn.Linear(hidden2,1)
        
    def forward(self,x):
        """
        Definition of forward pass.
        """
        x = self.relu1(self.linear1(x))
        x = self.relu2(self.linear2(x))
        x = self.linear3(x)
        return x
        
class DeepPlayerNetwork(nn.Module):
    """
    Class defining a deep neural network structure for predicting player salaries.
    Inherits from Module in PyTorch
    """

    def __init__(self,input_dimension,hidden_dimensions,dropout_rate):
        """
        Initilization of network.
        
        Arguments:
            self = Reference to self, Python class syntax
            input_dimension = Number of features given to the neural network
            hidden_dimensions = A list defining the number of neurons in each fully connected hidden layer
            dropout_rate = Dropout rate applied to each hidden layer
        """
        super(DeepPlayerNetwork,self).__init__()
        
        # Define a ModuleList to hold all the hidden layers
        self.layers = nn.ModuleList()
        previous_dimension = input_dimension
        
        # Add fully connected layers to the network
        for hidden_dimension in hidden_dimensions:
            self.layers.append(nn.Linear(previous_dimension, hidden_dimension))
            previous_dimension = hidden_dimension
        
        # Add the output layer
        self.layers.append(nn.Linear(previous_dimension, 1))
        
        # Define ReLU activation and dropout layer
        self.dropout = nn.Dropout(dropout_rate)
        self.relu = nn.ReLU()
        
        # Initialize the weights for the network
        self._init_weights()
        
    def _init_weights(self):
        """
        He initialization for hidden layers. Should provide the best performance for ReLU activation.
        Output layer with linear activation has uniform initialization instead.
        Bias is initialized to 0.
        """
        for i, layer in enumerate(self.layers):
        
            if i == len(self.layers) - 1:
                # Output layer - uniform initialization
                nn.init.uniform_(layer.weight, 0.0, 0.2)
            else:
                # Hidden layers - Kaiming normal (He)
                nn.init.kaiming_normal_(layer.weight, nonlinearity='relu')
                
            if layer.bias is not None:
                nn.init.zeros_(layer.bias)
        
    def forward(self,x):
        """
        Definition of forward pass.
        """
        
        # Loop through hidden layers and add ReLU activation and Dropout
        for layer in self.layers[:-1]:
            x = layer(x)
            x = self.relu(x)
            x = self.dropout(x)
            
        # Output layer without activation or Dropout
        x = self.layers[-1](x)
        return x
