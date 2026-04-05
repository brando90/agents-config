"""
Dummy experiment: train a 2-layer MLP on synthetic data.
Tests the full workflow: train → W&B log → W&B Report with URL.
Runs on CPU in seconds. No GPU needed.
"""

import argparse
import torch
import torch.nn as nn
import torch.optim as optim
import wandb
import wandb.apis.reports as wr


def make_synthetic_data(n=500, d=10, seed=42):
    """Binary classification: y = sign(x @ w_true + noise)."""
    torch.manual_seed(seed)
    w_true = torch.randn(d)
    X = torch.randn(n, d)
    noise = 0.1 * torch.randn(n)
    y = ((X @ w_true + noise) > 0).float()
    return X, y


class TinyMLP(nn.Module):
    def __init__(self, d_in=10, d_hidden=16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_in, d_hidden),
            nn.ReLU(),
            nn.Linear(d_hidden, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


def train(args):
    # --- Data ---
    X, y = make_synthetic_data(n=args.n, d=args.d, seed=args.seed)
    split = int(0.8 * len(X))
    X_train, y_train = X[:split], y[:split]
    X_val, y_val = X[split:], y[split:]

    # --- W&B init ---
    run = wandb.init(
        entity=args.wandb_entity,
        project=args.wandb_project,
        config=vars(args),
        name=f"dummy-mlp-seed{args.seed}",
    )

    # --- Model ---
    model = TinyMLP(d_in=args.d, d_hidden=args.hidden)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.BCEWithLogitsLoss()

    # --- Train loop ---
    for epoch in range(args.epochs):
        model.train()
        logits = model(X_train)
        loss = loss_fn(logits, y_train)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Val
        model.eval()
        with torch.no_grad():
            val_logits = model(X_val)
            val_loss = loss_fn(val_logits, y_val).item()
            val_preds = (val_logits > 0).float()
            val_acc = (val_preds == y_val).float().mean().item()

        wandb.log({
            "epoch": epoch,
            "train/loss": loss.item(),
            "val/loss": val_loss,
            "val/accuracy": val_acc,
        })

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{args.epochs} | train_loss={loss.item():.4f} | val_loss={val_loss:.4f} | val_acc={val_acc:.4f}")

    # --- Final metrics ---
    final_metrics = {"final/val_loss": val_loss, "final/val_accuracy": val_acc}
    wandb.log(final_metrics)
    print(f"\nFinal: val_loss={val_loss:.4f}, val_acc={val_acc:.4f}")

    # --- W&B Report ---
    report_url = None
    import os
    if os.environ.get("WANDB_MODE") != "offline":
        report_url = create_wandb_report(args, run)
    else:
        print("\nSkipping W&B Report (offline mode). Report creation requires WANDB_API_KEY.")

    wandb.finish()
    return report_url


def create_wandb_report(args, run):
    """Create a W&B Report and return its URL."""
    report = wr.Report(
        project=args.wandb_project,
        entity=args.wandb_entity,
        title=f"Dummy MLP Experiment — seed {args.seed}",
        description="Automated report from dummy experiment workflow test.",
        blocks=[
            wr.H1("Training Summary"),
            wr.P(f"2-layer MLP ({args.d}->{args.hidden}->1) trained on synthetic binary classification."),
            wr.P(f"Run: {run.name} | Epochs: {args.epochs} | LR: {args.lr}"),
            wr.H2("Loss Curves"),
            wr.PanelGrid(
                panels=[
                    wr.LinePlot(x="epoch", y=["train/loss", "val/loss"], title="Loss"),
                    wr.LinePlot(x="epoch", y=["val/accuracy"], title="Validation Accuracy"),
                ],
                runsets=[wr.Runset(
                    project=args.wandb_project,
                    entity=args.wandb_entity,
                    filters=f"Name = '{run.name}'",
                )],
            ),
        ],
    )
    report.save()
    report_url = report.url
    print(f"\nW&B Report URL: {report_url}")
    return report_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dummy MLP experiment")
    parser.add_argument("--n", type=int, default=500, help="Number of samples")
    parser.add_argument("--d", type=int, default=10, help="Input dimension")
    parser.add_argument("--hidden", type=int, default=16, help="Hidden layer size")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--wandb-entity", type=str, default="brando-su", help="W&B entity")
    parser.add_argument("--wandb-project", type=str, default="dummy-experiment-test", help="W&B project")
    args = parser.parse_args()

    report_url = train(args)
    if report_url:
        print(f"\nDone. Report: {report_url}")
    else:
        print("\nDone. Training complete (no report — offline or missing API key).")
