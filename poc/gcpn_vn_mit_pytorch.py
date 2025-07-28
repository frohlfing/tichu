"""
PyTorch-Implementation von GCPN+VN.

Hier ist ein einfaches Musterbeispiel für die kombinierte GCPN+VN Architektur.
"""

import torch
import torch.nn as nn


class HybridModelPyTorch(nn.Module):
    def __init__(self):
        super().__init__()

        # --- Shared Backbone ---
        self.backbone = nn.Sequential(
            nn.Linear(375, 1024),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(1024, 1024),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

        # --- Value Head ---
        self.value_head = nn.Sequential(
            nn.Linear(1024, 256),  # Input ist der Output des Backbones
            nn.ReLU(),
            nn.Linear(256, 1)  # Output ist 1 Neuron mit linearer Aktivierung (default)
        )

        # --- Policy Head ---
        # Input ist (Backbone_Output + RTG_Input) -> 1024 + 1 = 1025
        self.policy_head = nn.Sequential(
            nn.Linear(1025, 512),
            nn.ReLU(),
            nn.Linear(512, 57),
            nn.Sigmoid()  # Sigmoid am Ende
        )

    def forward(self, state_input, rtg_input):
        # Forward-Pass durch den Backbone
        shared_features = self.backbone(state_input)

        # Forward-Pass durch den Value Head
        value_output = self.value_head(shared_features)

        # Input für den Policy Head vorbereiten
        policy_input = torch.cat((shared_features, rtg_input), dim=1)

        # Forward-Pass durch den Policy Head
        policy_output = self.policy_head(policy_input)

        return policy_output, value_output


# Modell instanziieren
hybrid_model_pt = HybridModelPyTorch()
print(hybrid_model_pt)

# Der Trainings-Loop in PyTorch ist manueller.
# Du würdest die Verluste getrennt berechnen und dann addieren:
# policy_loss_fn = nn.BCELoss()
# value_loss_fn = nn.MSELoss()
# total_loss = policy_loss_fn(pred_policy, true_policy) + 0.5 * value_loss_fn(pred_value, true_value)
# total_loss.backward()
# optimizer.step()