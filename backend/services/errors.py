"""Shared exception types that the Flask error handlers turn into JSON responses."""


class ApiError(Exception):
    def __init__(self, message, status=400, code="bad_request", details=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details

    def to_dict(self):
        out = {"error": {"code": self.code, "message": self.message}}
        if self.details is not None:
            out["error"]["details"] = self.details
        return out


class DataError(ApiError):
    """Problem with the content/shape of a dataset."""

    def __init__(self, message, details=None):
        super().__init__(message, 422, "invalid_dataset", details)


class NoDatasetError(ApiError):
    def __init__(self):
        super().__init__(
            "No active dataset. Place mtsamples.csv in backend/data/ or upload "
            "a CSV on the Datasets page.",
            409,
            "no_active_dataset",
        )


class NeedsLabelsError(ApiError):
    def __init__(self):
        super().__init__(
            "This feature needs a 'medical_specialty' column with at least two "
            "specialties (each having 5+ distinct notes). The active dataset doesn't have one.",
            422,
            "labels_required",
        )
