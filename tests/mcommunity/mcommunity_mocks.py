from copy import deepcopy


def change_uniqname_on_mock(mock: list, new_uniqname: str):
    copy = deepcopy(mock)
    copy[0] = (f'uid={new_uniqname},ou=People,dc=umich,dc=edu', copy[0][1])
    copy[0][1]['mail'] = f'{new_uniqname}@umich.edu'
    copy[0][1]['uid'] = new_uniqname
    return copy


faculty_mock = [(
    'uid=nemcardf,ou=People,dc=umich,dc=edu',
    {
        'umichServiceEntitlement': [
            b'{"system":"papercut","changeDate":"20141201050814Z","foreignKey":"","eligibility":"yesDelay","status":"role","action":""}',
            b'{"system":"tdx","changeDate":"20200520160600Z","foreignKey":"5fd61fa7-035f-ea11-a81b-000d3a8e391e","eligibility":"yes","status":"active","action":""}',
            b'{"system":"box","changeDate":"20200815082046Z","foreignKey":"229315957","eligibility":"yesDelay","status":"active","action":""}',
            b'{"system":"canvas","changeDate":"20200821155033Z","foreignKey":"327664","eligibility":"yesImmed","status":"active","action":""}',
            b'{"system":"dropbox","changeDate":"20200929151240Z","foreignKey":"dbmid:x","eligibility":"yesDelay","status":"active","action":""}',
            b'{"system":"linkedinlearning","changeDate":"20201017144315Z","foreignKey":"","eligibility":"yesDelay","status":"","action":""}',
            b'{"system":"adobecc","changeDate":"20201017144315Z","foreignKey":"","eligibility":"cc","status":"","action":""}',
            b'{"system":"enterprise","changeDate":"20210721193419Z","eligibility":"yes","status":"active","action":""}'
        ],
        'umichInstRoles': [
            b'FacultyAA', b'RegularStaffDBRN', b'StudentFLNT', b'TemporaryStaffFLNT',
            b'SponsoredAffiliateAA', b'Retiree', b'AlumniAA'
        ],
        'entityid': [b'00000000'],
        'displayName': [b'Natalie Emcard'],
        'mail': [b'nemcardf@umich.edu'],
        'uid': [b'nemcardf'],
        'cn': [b'Natalie Emcard'],
        'test_str': b'test_decoding_str'
    }
)]

ineligible_service_entitlements = [
    b'{"system":"box","changeDate":"20220727160206Z","foreignKey":"","eligibility":"yesImmed","status":"","action":"add"}',
    b'{"system":"tdx","changeDate":"20220727160206Z","foreignKey":"","eligibility":"yes","status":"","action":"add"}',
    b'{"system":"dropbox","changeDate":"20220727160206Z","foreignKey":"","eligibility":"yesImmed","status":"","action":""}',
    b'{"system":"adobecc","changeDate":"20220727160206Z","foreignKey":"","eligibility":"acct","status":"","action":""}',
    b'{"system":"canvas","changeDate":"20220727160208Z","foreignKey":"746786","eligibility":"yesImmed","status":"active","action":""}',
    b'{"system":"papercut","changeDate":"20220727160210Z","foreignKey":"","eligibility":"yesImmed","status":"role","action":""}'
]

regstaff_mock = change_uniqname_on_mock(faculty_mock, 'nemcardrs')
regstaff_mock[0][1]['umichInstRoles'] = regstaff_mock[0][1]['umichInstRoles'][1:]

student_mock = change_uniqname_on_mock(regstaff_mock, 'nemcards')
student_mock[0][1]['umichInstRoles'] = student_mock[0][1]['umichInstRoles'][1:]

tempstaff_mock = change_uniqname_on_mock(student_mock, 'nemcardts')
tempstaff_mock[0][1]['umichInstRoles'] = tempstaff_mock[0][1]['umichInstRoles'][1:]

t1sponsored_mock = change_uniqname_on_mock(tempstaff_mock, 'nemcardsa1')
t1sponsored_mock[0][1]['umichInstRoles'] = t1sponsored_mock[0][1]['umichInstRoles'][1:]

t2sponsored_mock = change_uniqname_on_mock(t1sponsored_mock, 'nemcardsa2')
t2sponsored_mock[0][1]['entityid'] = [b'99000000']
t2sponsored_mock[0][1]['umichServiceEntitlement'] = ineligible_service_entitlements

t3sponsored_mock = change_uniqname_on_mock(t2sponsored_mock, 'um999999')

retiree_mock = change_uniqname_on_mock(faculty_mock, 'nemcardr')
retiree_mock[0][1]['umichInstRoles'] = retiree_mock[0][1]['umichInstRoles'][-2:]
retiree_mock[0][1]['umichServiceEntitlement'] = ineligible_service_entitlements

alumni_mock = change_uniqname_on_mock(retiree_mock, 'nemcarda')
alumni_mock[0][1]['umichInstRoles'] = alumni_mock[0][1]['umichInstRoles'][1:]

fake_mock = []
