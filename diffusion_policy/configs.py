from dataclasses import dataclass, field
from typing import Dict, Any

import hydra
from hydra.conf import HydraConf
from omegaconf import OmegaConf

OmegaConf.register_new_resolver("slash_to_dot", lambda dir: dir.replace("/", "."))
OmegaConf.register_new_resolver("checkpoint_name", lambda num_trajs: f"checkpoint_w_{num_trajs}_trajectories.pt")
OmegaConf.register_new_resolver("compute_epochs", lambda num_trajs: (110 - num_trajs) * 10)


@dataclass
class ExperimentHydraConfig(HydraConf):
    root_dir_name: str = "./outputs"
    new_override_dirname: str = "${slash_to_dot: ${hydra:job.override_dirname}}"
    run: Dict = field(default_factory=lambda: {
        # A more sophisticated example:
        # "dir": "${hydra:root_dir_name}/${hydra:new_override_dirname}/seed=${seed}/${now:%Y-%m-%d_%H-%M-%S}",
        # Default behavior logs by date and script name:
        "dir": "${hydra:root_dir_name}/${now:%Y-%m-%d_%H-%M-%S}",
    }
                      )

    sweep: Dict = field(default_factory=lambda: {
        "dir": "${..root_dir_name}/multirun/${now:%Y-%m-%d_%H-%M-%S}",
        "subdir": "${hydra:new_override_dirname}",
    }
                        )

    job: Dict = field(default_factory=lambda: {
        "config": {
            "override_dirname": {
                "exclude_keys": [
                    "sim_device",
                    "rl_device",
                    "headless",
                ]
            }
        },
        "chdir": True
    })

@dataclass
class DatasetConfig:
    # SERL type is the data from record_demos, HDF5 is the type outputed from robomimic, Jacob is the
    # data from process_data.py
    type: str = "Jacob"  # Options are SERL or HDF5 or Jacob or D4RL
    dataset_path: str = "${hydra:runtime.cwd}/data/peg_data.pkl" # Path to your training dataset
    num_traj: int = -1 # Number of trajectories to train on. -1 is all of them

    # The keys from observations that we use for the inputs to our model
    image_keys: list = field(default_factory=lambda: ['agentview_image', 'robot0_eye_in_hand_image', 'birdview_image'])
    state_keys: list = field(default_factory=lambda: ['robot0_proprio-state', 'object-state'])

@dataclass
class DiffusionModelRunConfig:
    hydra: ExperimentHydraConfig = field(default_factory=ExperimentHydraConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    device: str = "cuda"
    checkpoint_path: str = "${hydra:runtime.cwd}/jacob_dataformat_image_propreo.pt"

    batch_size: int = 256//2
    num_epochs: int = 16

    # If with_state, uses the state keys. If without doesn't and state len does not matter
    with_state: bool = False
    # Length of the concatenated state
    state_len: int = 42
    with_image: bool = True
    # Number of images in the observation. Should be equal to the length of image_keys
    num_cameras: int = 3

    action_dim: int = 7
    pred_horizon: int = 12
    obs_horizon: int = 4
    action_horizon: int = 8
    num_diffusion_iters: int = 100
    num_eval_diffusion_iters: int = 100

    noise_pred_net: dict[str, Any] = field(default_factory=lambda: {})



