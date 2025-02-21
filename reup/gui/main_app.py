def __init__(self, root):
    self.root = root
    self.after_ids = []  # Track scheduled tasks
    # ... rest of init ...


def schedule_task(self, delay, callback):
    """Schedule a task and track its ID."""
    after_id = self.root.after(delay, callback)
    self.after_ids.append(after_id)
    return after_id


def cleanup(self):
    """Cancel all scheduled tasks."""
    for after_id in self.after_ids:
        self.root.after_cancel(after_id)
    self.after_ids.clear()


def __del__(self):
    """Ensure cleanup on deletion."""
    self.cleanup()
