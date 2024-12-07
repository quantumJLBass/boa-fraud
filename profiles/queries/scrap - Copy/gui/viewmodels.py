class GUIViewModel:
    """Base class for GUI view models."""
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def load_data(self):
        raise NotImplementedError("Subclasses must implement load_data method.")

    def save_data(self):
        raise NotImplementedError("Subclasses must implement save_data method.")

class URLViewModel(GUIViewModel):
    """View model for URL data."""
    def load_data(self, url_id):
        with gs.read() as session:
            url = self.model.get_by_id(session, url_id)
            self.view.populate(url)

    def save_data(self, url, company, jurisdiction, completed):
        with gs.write() as session:
            url_obj = self.model.get_by_id(session, url.id)
            url_obj.url = url
            url_obj.company_number = company
            url_obj.jurisdiction_code = jurisdiction
            url_obj.completed = completed
            url_obj.save(session)