from lxml import etree
import pytest
from lessonai.parsers.office_math import omml_to_latex

NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'


def test_omml_fraction_and_power():
    xml = f"""
    <m:oMath xmlns:m="{NS}">
        <m:f>
            <m:num><m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup></m:num>
            <m:den><m:r><m:t>3</m:t></m:r></m:den>
        </m:f>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml)) == r'\frac{{x}^{2}}{3}'


def test_omml_sub_and_sub_sup():
    xml = f"""
    <m:oMath xmlns:m="{NS}">
        <m:sSubSup>
            <m:e><m:r><m:t>x</m:t></m:r></m:e>
            <m:sub><m:r><m:t>1</m:t></m:r></m:sub>
            <m:sup><m:r><m:t>2</m:t></m:r></m:sup>
        </m:sSubSup>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml)) == r'{x}_{1}^{2}'


def test_omml_radical_square_and_cubic():
    # Square root (degHide)
    xml_sqrt = f"""
    <m:oMath xmlns:m="{NS}">
        <m:rad>
            <m:radPr><m:degHide m:val="on"/></m:radPr>
            <m:deg/>
            <m:e><m:r><m:t>x+1</m:t></m:r></m:e>
        </m:rad>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_sqrt)) == r'\sqrt{x+1}'

    # Cubic root
    xml_cbrt = f"""
    <m:oMath xmlns:m="{NS}">
        <m:rad>
            <m:deg><m:r><m:t>3</m:t></m:r></m:deg>
            <m:e><m:r><m:t>x</m:t></m:r></m:e>
        </m:rad>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_cbrt)) == r'\sqrt[3]{x}'


def test_omml_accent_vector_and_hat():
    # Vector: chr="⃗"
    xml_vec = f"""
    <m:oMath xmlns:m="{NS}">
        <m:acc>
            <m:accPr><m:chr m:val="⃗"/></m:accPr>
            <m:e><m:r><m:t>u</m:t></m:r></m:e>
        </m:acc>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_vec)) == r'\vec{u}'

    # Hat: chr="̂"
    xml_hat = f"""
    <m:oMath xmlns:m="{NS}">
        <m:acc>
            <m:accPr><m:chr m:val="̂"/></m:accPr>
            <m:e><m:r><m:t>A</m:t></m:r></m:e>
        </m:acc>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_hat)) == r'\hat{A}'

    # Empty acc without <m:e> raises ValueError containing 'chưa hỗ trợ'
    with pytest.raises(ValueError, match='chưa hỗ trợ'):
        omml_to_latex(etree.fromstring(f'<m:oMath xmlns:m="{NS}"><m:acc/></m:oMath>'))


def test_omml_delimiter_parentheses_and_cases():
    # Standard parentheses: (a, b)
    xml_paren = f"""
    <m:oMath xmlns:m="{NS}">
        <m:d>
            <m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/><m:sepChr m:val=";"/></m:dPr>
            <m:e><m:r><m:t>1</m:t></m:r></m:e>
            <m:e><m:r><m:t>2</m:t></m:r></m:e>
        </m:d>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_paren)) == r'\left(1; 2\right)'

    # System of equations brace: begChr="{", endChr=""
    xml_cases = f"""
    <m:oMath xmlns:m="{NS}">
        <m:d>
            <m:dPr><m:begChr m:val="{{"/><m:endChr m:val=""/></m:dPr>
            <m:e>
                <m:eqArr>
                    <m:e><m:r><m:t>x+y=1</m:t></m:r></m:e>
                    <m:e><m:r><m:t>x-y=0</m:t></m:r></m:e>
                </m:eqArr>
            </m:e>
        </m:d>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_cases)) == (
        r'\left\{\begin{aligned} x+y=1 \\ x-y=0 \end{aligned}\right.'
    )


def test_omml_function_and_limit():
    # Function sin(x)
    xml_func = f"""
    <m:oMath xmlns:m="{NS}">
        <m:func>
            <m:fName><m:r><m:t>sin</m:t></m:r></m:fName>
            <m:e><m:r><m:t>x</m:t></m:r></m:e>
        </m:func>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_func)) == r'\sin x'

    # Limit: lim_{x -> 0} f(x)
    xml_lim = f"""
    <m:oMath xmlns:m="{NS}">
        <m:limLow>
            <m:e><m:r><m:t>lim</m:t></m:r></m:e>
            <m:lim><m:r><m:t>x→0</m:t></m:r></m:lim>
        </m:limLow>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_lim)) == r'\lim_{x\to 0}'


def test_omml_integral_and_sum():
    # Integral: \int_{0}^{1} x
    xml_int = f"""
    <m:oMath xmlns:m="{NS}">
        <m:nary>
            <m:naryPr><m:chr m:val="∫"/></m:naryPr>
            <m:sub><m:r><m:t>0</m:t></m:r></m:sub>
            <m:sup><m:r><m:t>1</m:t></m:r></m:sup>
            <m:e><m:r><m:t>xdx</m:t></m:r></m:e>
        </m:nary>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_int)) == r'\int_{0}^{1} xdx'


def test_omml_unicode_alphanumerics_normalization():
    # Mathematical bold italic small x: 𝑥 (U+1D465) and minus − (U+2212)
    xml_unicode = f"""
    <m:oMath xmlns:m="{NS}">
        <m:r><m:t>𝑥−𝟐≤0</m:t></m:r>
    </m:oMath>
    """
    assert omml_to_latex(etree.fromstring(xml_unicode)) == r'x-2\le 0'


def test_omml_empty_raises_value_error():
    with pytest.raises(ValueError, match='Công thức rỗng'):
        omml_to_latex(etree.fromstring(f'<m:oMath xmlns:m="{NS}"/>'))
