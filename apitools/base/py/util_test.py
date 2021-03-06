#!/usr/bin/env python


from protorpc import messages
import unittest2

from apitools.base.py import encoding
from apitools.base.py import exceptions
from apitools.base.py import util


class MockedMethodConfig(object):

  def __init__(self, relative_path, path_params):
    self.relative_path = relative_path
    self.path_params = path_params


class MessageWithRemappings(messages.Message):

  class AnEnum(messages.Enum):
    value_one = 1
    value_two = 2

  str_field = messages.StringField(1)
  enum_field = messages.EnumField('AnEnum', 2)


encoding.AddCustomJsonFieldMapping(
    MessageWithRemappings, 'str_field', 'path_field')
encoding.AddCustomJsonEnumMapping(
    MessageWithRemappings.AnEnum, 'value_one', 'ONE')


class UtilTest(unittest2.TestCase):

  def testExpand(self):
    method_config_xy = MockedMethodConfig(relative_path='{x}/y/{z}',
                                          path_params=['x', 'z'])
    self.assertEquals(
        util.ExpandRelativePath(method_config_xy, {'x': '1', 'z': '2'}),
        '1/y/2')
    self.assertEquals(
        util.ExpandRelativePath(
            method_config_xy,
            {'x': '1', 'z': '2'},
            relative_path='{x}/y/{z}/q'),
        '1/y/2/q')

  def testReservedExpansion(self):
    method_config_reserved = MockedMethodConfig(relative_path='{+x}/baz',
                                                path_params=['x'])
    self.assertEquals('foo/:bar:/baz', util.ExpandRelativePath(
        method_config_reserved, {'x': 'foo/:bar:'}))
    method_config_no_reserved = MockedMethodConfig(relative_path='{x}/baz',
                                                   path_params=['x'])
    self.assertEquals('foo%2F%3Abar%3A/baz', util.ExpandRelativePath(
        method_config_no_reserved, {'x': 'foo/:bar:'}))

  def testCalculateWaitForRetry(self):
    self.assertTrue(util.CalculateWaitForRetry(1) in range(1, 4))
    self.assertTrue(util.CalculateWaitForRetry(2) in range(2, 7))
    self.assertTrue(util.CalculateWaitForRetry(3) in range(4, 13))
    self.assertTrue(util.CalculateWaitForRetry(4) in range(8, 25))

    self.assertEquals(10, util.CalculateWaitForRetry(5, max_wait=10))

    self.assertGreater(util.CalculateWaitForRetry(0), 0)

  def testTypecheck(self):

    class Class1(object):
      pass

    class Class2(object):
      pass

    class Class3(object):
      pass

    instance_of_class1 = Class1()

    self.assertEquals(
        instance_of_class1, util.Typecheck(instance_of_class1, Class1))

    self.assertEquals(
        instance_of_class1,
        util.Typecheck(instance_of_class1, ((Class1, Class2), Class3)))

    self.assertEquals(
        instance_of_class1,
        util.Typecheck(instance_of_class1, (Class1, (Class2, Class3))))

    self.assertEquals(
        instance_of_class1,
        util.Typecheck(instance_of_class1, Class1, 'message'))

    self.assertEquals(
        instance_of_class1,
        util.Typecheck(
            instance_of_class1, ((Class1, Class2), Class3), 'message'))

    self.assertEquals(
        instance_of_class1,
        util.Typecheck(
            instance_of_class1, (Class1, (Class2, Class3)), 'message'))

    try:
      util.Typecheck(instance_of_class1, Class2)
      self.fail('Type mismatch not detected when called with 2 arguments')
    except exceptions.TypecheckError:
      pass  # expected

    try:
      util.Typecheck(instance_of_class1, (Class2, Class3))
      self.fail(
          'Type mismatch not detected when called with 2 arguments including '
          'type tuple')
    except exceptions.TypecheckError:
      pass  # expected

    try:
      util.Typecheck(instance_of_class1, Class2, 'message')
      self.fail('Type mismatch not detected when called with 3 arguments')
    except exceptions.TypecheckError:
      pass  # expected

    try:
      util.Typecheck(instance_of_class1, (Class2, Class3), 'message')
      self.fail(
          'Type mismatch not detected when called with 3 arguments including '
          'type tuple')
    except exceptions.TypecheckError:
      pass  # expected

  def testAcceptableMimeType(self):
    valid_pairs = (
        ('*', 'text/plain'),
        ('*/*', 'text/plain'),
        ('text/*', 'text/plain'),
        ('*/plain', 'text/plain'),
        ('text/plain', 'text/plain'),
    )

    for accept, mime_type in valid_pairs:
      self.assertTrue(util.AcceptableMimeType([accept], mime_type))

    invalid_pairs = (
        ('text/*', 'application/json'),
        ('text/plain', 'application/json'),
    )

    for accept, mime_type in invalid_pairs:
      self.assertFalse(util.AcceptableMimeType([accept], mime_type))

    self.assertTrue(util.AcceptableMimeType(['application/json', '*/*'],
                                            'text/plain'))
    self.assertFalse(util.AcceptableMimeType(['application/json', 'img/*'],
                                             'text/plain'))

  def testUnsupportedMimeType(self):
    self.assertRaises(
        exceptions.GeneratedClientError,
        util.AcceptableMimeType, ['text/html;q=0.9'], 'text/html')

  def testMapRequestParams(self):
    params = {
        'str_field': 'foo',
        'enum_field': MessageWithRemappings.AnEnum.value_one,
    }
    remapped_params = {
        'path_field': 'foo',
        'enum_field': 'ONE',
    }
    self.assertEqual(remapped_params,
                     util.MapRequestParams(params, MessageWithRemappings))

    params['enum_field'] = MessageWithRemappings.AnEnum.value_two
    remapped_params['enum_field'] = 'value_two'
    self.assertEqual(remapped_params,
                     util.MapRequestParams(params, MessageWithRemappings))

  def testMapParamNames(self):
    params = ['path_field', 'enum_field']
    remapped_params = ['str_field', 'enum_field']
    self.assertEqual(remapped_params,
                     util.MapParamNames(params, MessageWithRemappings))

if __name__ == '__main__':
  unittest2.main()
