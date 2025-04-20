class SandboxRecordsMixin:
    def list_sandboxes(self) -> list:
        sandboxes = []
        for sandbox in self.sandbox_client.containers.list(all=True, filters={"label": "python-sandbox"}):
            sandbox_info = {
                "sandbox_id": sandbox.id,
                "name": sandbox.name,
                "status": sandbox.status,
                "image": sandbox.image.tags[0] if sandbox.image.tags else sandbox.image.short_id,
                "created": sandbox.attrs["Created"],
                "last_used": self.sandbox_last_used.get(sandbox.id),
            }
            sandboxes.append(sandbox_info)
        return sandboxes
