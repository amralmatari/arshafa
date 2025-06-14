from sqlalchemy.ext.hybrid import hybrid_property

# Instead of something like:
# @some_property  # INCORRECT - this decorator doesn't exist
def property_name(self):
    return self.value

# Use the correct syntax:
@property
def property_name(self):
    return self.value

# Or for SQLAlchemy hybrid_property:
@hybrid_property
def property_name(self):
    return self.value

