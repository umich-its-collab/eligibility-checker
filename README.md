# eligibility-checker
Check eligibility in the same way across all Collab services

## License and Use
This package is NOT licensed for open-source use. It is only available for the University of Michigan ITS 
Collaboration Services team.

## How to Use
1. Add the following as a new line to your project's `requirements.txt` file, where the text after the `@` and before 
the `#` is the name of the [tag/version](https://github.com/umich-its-collab/eligibility-checker/tags) of 
eligibility-checker you want. For example, the tag set here is `v0.1`.
`-e git+https://github.com/umich-its-collab/eligibility-checker.git@v0.1#egg=eligibility_checker`
2. Ensure your virtual environment is activated, then run the command `pip install -r requirements.txt`
3. Create a subclass of `EligibilityChecker`. If this is a Django project, the ideal location is in the project package
(i.e. the same directory as `settings.py`) in a separate clearly named file, such as `zoom_eligibility_checker.py`. 
Ensure the following attributes are set properly:
   1. *service_friendly*: should be the friendly capital case name of the service (ex: Google, Microsoft Teams, Slack)
   2. *service_entitlement*: the string to check for in the "system" key of a uSE dictionary. Leave as "enterprise" for 
   services that rely on the enterprise uSE (as of 8/2022 this is true for Dropbox, Slack, and Zoom). Set as None for 
   services that do not rely on any uSE (as of 8/2022 this is true for Google and Microsoft). Can be set to a different 
   service than "enterprise" if in the future we ever use another uSE but right now we do not.
   3. *override_groups*: should always contain `'collab-iam-admins'` to avoid deactivating Collab team members' admin 
   accounts; append any other override groups for the service (ex: `'zoom-iam-primary'`, `'slack-iam-primary'`)
   4. *eligible_affiliations_minus_sa*: all affiliations (not including `SponsoredAffiliate`) that should be eligible 
   for this service. For services that use the enterprise uSE, this shouldn't need to change. For Google, this should 
   also include `'Retiree'` and `'Alumni'`.
   5. *eligible_sa_types:* a list of integers for sponsored affiliate types that should be considered eligible for this 
   service. Default is `[1]`.
4. In the context that you need it, create an instance of your `EligibilityChecker` child class and pass in the 
MCommunity app cname and secret as parameters.
   1. *Example*: `EligibilityCheckerSubClass('ITS-Dropbox-McDirApp001', '0xjemsozj4')`
5. For each user that you need to check eligibility for in this context, use the same class instance and pass the 
uniqname to the `check_eligibility` method.

## Examples
Below is an example of what you might enter into the file described in step 3 above.

```python
from eligibility_checker.checker import EligibilityChecker


class ZoomEligibilityChecker(EligibilityChecker):
   service_friendly = 'Zoom'
   service_entitlement = 'enterprise'  # This is default, but just setting to be very explicit

   override_groups = ['collab-iam-admins', 'zoom-iam-primary']
```

Below is an example of how you might instantiate and use `ZoomEligibilityChecker`
```python
from zoominfo.zoom_eligibility_checker import ZoomEligibilityChecker

checker = ZoomEligibilityChecker(settings.MCOMM_APP_NAME, settings.MCOMM_APP_SECRET)
users = ['user1', 'user2', 'user3', 'user4', 'user5']

for user in users:
    response = checker.check_eligibility(user)
    print(response.eligible)
```
