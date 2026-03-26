#!/bin/bash
#SBATCH -N 1                                  #  --nodes 
#SBATCH -n 1                                  # --ntasks (default = 1)  (number of tasks / processes)
#SBATCH -p cs05r                      # --partition ( Partition name  / queue)
#SBATCH --time=24:00:00            # Time limit (days-hh:mm:ss) # 08:00:00  
#SBATCH --job-name updtFSys                  # Job name
#SBATCH --output ./slurm/logs/updtFileSys_pt2-batch-job.out # ./logs/batch-job_%j.out             # Output file
#SBATCH --error ./slurm/logs/updtFileSys_pt2-batch-job.err # ./logs/batch-job_%j.err    
#SBATCH --mem=16G                   # Memory per node
#SBATCH --cpus-per-task=8       # Each task gets 4 CPU cores


source ~/MyDB/xaidar/.venv/bin/activate
echo "Hostname: $HOSTNAME"
echo "Job ID: $SLURM_JOB_ID"
python -u ~/MyDB/xaidar/xaidar/tasks/updateFileSys.py

