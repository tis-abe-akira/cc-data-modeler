"""
Nablarch Utilities Unit Tests

Tests for:
- DomainInferrer
- PackageNameInferrer
- DomainConstraintInferrer
"""

import unittest
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from nablarch_utils import DomainInferrer, PackageNameInferrer, DomainConstraintInferrer


class TestDomainInferrer(unittest.TestCase):
    """Test DomainInferrer class"""

    def test_simple_field_name(self):
        """Test simple PascalCase to camelCase conversion"""
        self.assertEqual(DomainInferrer.infer_domain_name('CompanyName'), 'companyName')
        self.assertEqual(DomainInferrer.infer_domain_name('EmailAddress'), 'emailAddress')
        self.assertEqual(DomainInferrer.infer_domain_name('StartDateTime'), 'startDateTime')

    def test_id_field(self):
        """Test ID field preservation (uppercase ID)"""
        self.assertEqual(DomainInferrer.infer_domain_name('ProjectID'), 'projectID')
        self.assertEqual(DomainInferrer.infer_domain_name('CustomerID'), 'customerID')
        self.assertEqual(DomainInferrer.infer_domain_name('PersonID'), 'personID')

    def test_single_id(self):
        """Test field name that is only 'ID'"""
        self.assertEqual(DomainInferrer.infer_domain_name('ID'), 'id')

    def test_empty_field_name(self):
        """Test empty field name"""
        self.assertEqual(DomainInferrer.infer_domain_name(''), '')

    def test_single_character(self):
        """Test single character field name"""
        self.assertEqual(DomainInferrer.infer_domain_name('A'), 'a')


class TestPackageNameInferrer(unittest.TestCase):
    """Test PackageNameInferrer class"""

    def test_resource_entity(self):
        """Test resource entity to package name"""
        self.assertEqual(PackageNameInferrer.infer_package_name('Project', 'resource'), 'projects')
        self.assertEqual(PackageNameInferrer.infer_package_name('Customer', 'resource'), 'customers')
        self.assertEqual(PackageNameInferrer.infer_package_name('Person', 'resource'), 'persons')

    def test_event_entity_start(self):
        """Test event entity (Start suffix) to package name"""
        self.assertEqual(PackageNameInferrer.infer_package_name('ProjectStart', 'event'), 'projects')
        self.assertEqual(PackageNameInferrer.infer_package_name('CustomerComplete', 'event'), 'customers')

    def test_event_entity_assign(self):
        """Test event entity (Assign suffix) to package name"""
        self.assertEqual(PackageNameInferrer.infer_package_name('PersonAssign', 'event'), 'persons')
        self.assertEqual(PackageNameInferrer.infer_package_name('ProjectAssign', 'event'), 'projects')

    def test_event_entity_replace(self):
        """Test event entity (Replace suffix) to package name"""
        self.assertEqual(PackageNameInferrer.infer_package_name('PersonReplace', 'event'), 'persons')

    def test_event_entity_evaluate(self):
        """Test event entity (Evaluate suffix) to package name"""
        self.assertEqual(PackageNameInferrer.infer_package_name('RiskEvaluate', 'event'), 'risks')

    def test_pluralization(self):
        """Test pluralization rules"""
        self.assertEqual(PackageNameInferrer._pluralize('project'), 'projects')
        self.assertEqual(PackageNameInferrer._pluralize('person'), 'persons')
        self.assertEqual(PackageNameInferrer._pluralize('customer'), 'customers')

    def test_pluralization_y_ending(self):
        """Test pluralization for words ending in 'y'"""
        self.assertEqual(PackageNameInferrer._pluralize('category'), 'categories')
        self.assertEqual(PackageNameInferrer._pluralize('company'), 'companies')

    def test_to_snake_case(self):
        """Test PascalCase to snake_case conversion"""
        self.assertEqual(PackageNameInferrer._to_snake_case('ProjectStart'), 'project_start')
        self.assertEqual(PackageNameInferrer._to_snake_case('PersonAssign'), 'person_assign')
        self.assertEqual(PackageNameInferrer._to_snake_case('ProjectID'), 'project_id')

    def test_empty_entity_name(self):
        """Test empty entity name"""
        self.assertEqual(PackageNameInferrer.infer_package_name('', 'resource'), '')


class TestDomainConstraintInferrer(unittest.TestCase):
    """Test DomainConstraintInferrer class"""

    def test_varchar_constraint(self):
        """Test VARCHAR type constraint inference"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'CompanyName', 'VARCHAR(256)', '会社名', nullable=False
        )
        self.assertEqual(constraints['type'], '文字列')
        self.assertEqual(constraints['max_length'], 256)
        self.assertTrue(constraints['required'])

    def test_decimal_constraint(self):
        """Test DECIMAL type constraint inference"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'ContractAmount', 'DECIMAL(15,2)', '契約金額', nullable=False
        )
        self.assertEqual(constraints['type'], '数値（DECIMAL）')
        self.assertEqual(constraints['precision'], 15)
        self.assertEqual(constraints['scale'], 2)
        self.assertEqual(constraints['integer_digits'], 13)
        self.assertEqual(constraints['decimal_digits'], 2)
        self.assertTrue(constraints['required'])

    def test_int_constraint(self):
        """Test INT type constraint inference"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'ProjectID', 'INT', 'プロジェクトID', nullable=False
        )
        self.assertEqual(constraints['type'], '整数')
        self.assertEqual(constraints['charset'], 'ASCII文字（英数字、記号）')  # ID field
        self.assertTrue(constraints['required'])

    def test_timestamp_constraint(self):
        """Test TIMESTAMP type constraint inference"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'StartDateTime', 'TIMESTAMP', '開始日時', nullable=False
        )
        self.assertEqual(constraints['type'], '日時')
        self.assertEqual(constraints['format'], 'date-time')
        self.assertTrue(constraints['required'])

    def test_date_constraint(self):
        """Test DATE type constraint inference"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'BirthDate', 'DATE', '生年月日', nullable=True
        )
        self.assertEqual(constraints['type'], '日付')
        self.assertEqual(constraints['format'], 'date')
        self.assertFalse(constraints['required'])  # nullable=True

    def test_boolean_constraint(self):
        """Test BOOLEAN type constraint inference"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'IsActive', 'BOOLEAN', '有効フラグ', nullable=False
        )
        self.assertEqual(constraints['type'], 'ブール値')
        self.assertTrue(constraints['required'])

    def test_email_format_inference(self):
        """Test email format inference from field name"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'EmailAddress', 'VARCHAR(64)', 'メールアドレス', nullable=False
        )
        self.assertEqual(constraints['format'], 'email')
        self.assertEqual(constraints['format_description'], 'メールアドレス形式（RFC 5322準拠）')
        self.assertEqual(constraints['charset'], 'ASCII文字')

    def test_url_format_inference(self):
        """Test URL format inference from field name"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'WebsiteURL', 'VARCHAR(256)', 'ウェブサイトURL', nullable=True
        )
        self.assertEqual(constraints['format'], 'uri')
        self.assertEqual(constraints['format_description'], 'URL形式')
        self.assertEqual(constraints['charset'], 'ASCII文字')
        self.assertFalse(constraints['required'])

    def test_phone_format_inference(self):
        """Test phone number format inference from field name"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'PhoneNumber', 'VARCHAR(15)', '電話番号', nullable=True
        )
        self.assertEqual(constraints['pattern'], r'^\d{2,4}-?\d{2,4}-?\d{4}$')
        self.assertEqual(constraints['format_description'], '電話番号形式（ハイフンあり/なし）')
        self.assertFalse(constraints['required'])

    def test_postal_code_inference(self):
        """Test postal code format inference from field name"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'PostalCode', 'VARCHAR(8)', '郵便番号', nullable=False
        )
        self.assertEqual(constraints['pattern'], r'^\d{3}-?\d{4}$')
        self.assertEqual(constraints['format_description'], '郵便番号形式（7桁、ハイフンあり/なし）')
        self.assertTrue(constraints['required'])

    def test_japanese_name_charset(self):
        """Test charset inference for Japanese field names"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'CompanyName', 'VARCHAR(256)', '会社名', nullable=False
        )
        self.assertEqual(constraints['charset'], 'システム許容文字（全角・半角英数字、ひらがな、カタカナ、漢字、記号）')

    def test_id_field_charset(self):
        """Test charset inference for ID fields"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'ProjectID', 'INT', 'プロジェクトID', nullable=False
        )
        self.assertEqual(constraints['charset'], 'ASCII文字（英数字、記号）')

    def test_code_field_charset(self):
        """Test charset inference for code fields"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'ProductCode', 'VARCHAR(20)', '商品コード', nullable=False
        )
        self.assertEqual(constraints['charset'], 'ASCII文字（英数字、記号）')

    def test_primary_key_not_required(self):
        """Test that primary key fields are not marked as required"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'ProjectID', 'INT', 'プロジェクトID', nullable=False, is_primary_key=True
        )
        self.assertFalse(constraints['required'])  # Primary key should not be required in request

    def test_nullable_field_not_required(self):
        """Test that nullable fields are not required"""
        constraints = DomainConstraintInferrer.infer_constraints(
            'Description', 'VARCHAR(1000)', '説明', nullable=True
        )
        self.assertFalse(constraints['required'])

    def test_parse_sql_type_empty(self):
        """Test empty SQL type"""
        result = DomainConstraintInferrer._parse_sql_type('')
        self.assertEqual(result['type'], '文字列')

    def test_parse_sql_type_text(self):
        """Test TEXT SQL type"""
        result = DomainConstraintInferrer._parse_sql_type('TEXT')
        self.assertEqual(result['type'], '文字列')

    def test_infer_charset_empty_name(self):
        """Test charset inference with empty field name"""
        charset = DomainConstraintInferrer._infer_charset('', '')
        self.assertEqual(charset, 'ASCII文字（英数字、記号）')


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDomainInferrer))
    suite.addTests(loader.loadTestsFromTestCase(TestPackageNameInferrer))
    suite.addTests(loader.loadTestsFromTestCase(TestDomainConstraintInferrer))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
