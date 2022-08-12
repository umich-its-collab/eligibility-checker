# eligibility-checker
Check eligibility in the same way across all Collab services

# How to Use
1. [insert instructions on installing]
2. Create a subclass of EligibilityChecker and ensure the following attributes are set properly:
   1. service_friendly: should be the friendly capital case name of the service (ex: Google, Microsoft Teams, Slack)
   2. service_entitlement: the string to check for in the "system" key of a uSE dictionary. Leave as "enterprise" for 
   services that rely on the enterprise uSE (as of 8/2022 this is true for Dropbox, Slack, and Zoom). Set as None for 
   services that do not rely on any uSE (as of 8/2022 this is true for Google and Microsoft). Can be set to a different 
   service than "enterprise" if in the future we ever use another uSE but right now we do not.
   3. override_groups: should always contain `'collab-iam-admins'` to avoid deactivating Collab team members' admin 
   accounts; append any other override groups for the service (ex: `'zoom-iam-primary'`, `'slack-iam-primary'`)
   4. eligible_affiliations_minus_sa: all affiliations (not including `SponsoredAffiliate`) that should be eligible for 
   this service. For services that use the enterprise uSE, this shouldn't need to change. For Google, this should also 
   include `'Retiree'` and `'Alumni'`.
   5. eligible_sa_types: a list of integers for sponsored affiliate types that should be considered eligible for this 
   service. Default is `[1]`.
3. Create an instance of your EligibilityChecker child class and pass in the MCommunity app cname and secret as 
parameters.
   1. Example: `EligibilityCheckerSubClass('ITS-Dropbox-McDirApp001', '0xjemsozj4'')`
