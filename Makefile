.PHONY: train train-advanced report

train:
	cd backend && python train_pipeline.py

train-advanced:
	cd backend && python -m ml.train_advanced

report:
	cd backend && python -m ml.generate_report
