#!/usr/bin/env python

# Copyright (c) 2017 Timothy Savannah under LGPL version 2.1. See LICENSE for more information.
#
# TestIRForeignLinkField - Test default values for fields
#

# vim: set ts=4 sw=4 st=4 expandtab

# Import and apply the properties (like Redis connection parameters) for this test.
import TestProperties

import base64
import sys
import subprocess

from IndexedRedis import IndexedRedisModel, irNull
from IndexedRedis.compat_str import tobytes
from IndexedRedis.fields import IRForeignLinkField, IRField, IRForeignLinkField

# vim: ts=4 sw=4 expandtab

class TestIRForeignLinkField(object):
    '''
        TestIRForeignLinkField - Test base64 field
    '''

    KEEP_DATA = False

    def setup_method(self, testMethod):
        '''
            setup_method - Called before every method. Should set "self.model" to the model needed for the test.
  
            @param testMethod - Instance method of test about to be called.
        '''
        self.models = {}

        class Model_RefedModel(IndexedRedisModel):

            FIELDS = [
                IRField('name'),
                IRField('strVal'),
                IRField('intVal', valueType=int)
            ]

            INDEXED_FIELDS = ['name']

            KEY_NAME = 'TestIRForeignLinkField__RefedModel1'

        self.models['RefedModel'] = Model_RefedModel

        class Model_MainModel(IndexedRedisModel):
            
            FIELDS = [
                IRField('name'),
                IRField('value'),
                IRForeignLinkField('other', Model_RefedModel),
            ]

            INDEXED_FIELDS = ['name']

            KEY_NAME='TestIRForeignLinkField__MainModel1'

        self.models['MainModel'] = Model_MainModel

        if testMethod == self.test_filterOnModel:
            class Model_MainModelIndexed(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRField('value'),
                    IRForeignLinkField('other', Model_RefedModel),
                ]

                INDEXED_FIELDS = ['name', 'other']

                KEY_NAME='TestIRForeignLinkField__MainModelIndexed1'

            self.models['MainModel'] = Model_MainModelIndexed

        if testMethod in (self.test_cascadeSave, self.test_cascadeFetch, self.test_reload):
            class Model_PreMainModel(IndexedRedisModel):
                FIELDS = [
                    IRField('name'),
                    IRField('value'),
                    IRForeignLinkField('main', Model_MainModel),
                ]

                INDEXED_FIELDS = ['name']

                KEY_NAME = 'TestIRForeignLinkField__PreMainModel1'

            self.models['PreMainModel'] = Model_PreMainModel


        # If KEEP_DATA is False (debug flag), then delete all objects before so prior test doesn't interfere
        if self.KEEP_DATA is False and self.models:
            for model in self.models.values():
                model.deleter.destroyModel()

    def teardown_method(self, testMethod):
        '''
            teardown_method - Called after every method.

                If self.model is set, will delete all objects relating to that model. To retain objects for debugging, set TestIRField.KEEP_DATA to True.
        '''

        if self.KEEP_DATA is False and self.models:
            for model in self.models.values():
                model.deleter.destroyModel()


    def test_general(self):
        
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj = RefedModel(name='rone', strVal='hello', intVal=1)
        ids = refObj.save(cascadeSave=False)
        assert ids and ids[0]

        mainObj = MainModel(name='one', value='cheese', other=ids[0])

        mainObj.save(cascadeSave=False)

        assert isinstance(mainObj.other, RefedModel) , 'Expected access of object to return object'

        assert mainObj.other__id == ids[0] , 'Expected __id access to return the object\'s id.'

        fetchedObj = MainModel.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        assert isinstance(fetchedObj.other, RefedModel) , 'After save-and-fetch, expected access of object to return object'

        assert fetchedObj.other__id == ids[0] , 'After save-and-fetch, expected __id access to return the object\'s id.'

    
    def test_disconnectAssociation(self):

        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj = RefedModel(name='rone', strVal='hello', intVal=1)
        ids = refObj.save(cascadeSave=False)
        assert ids and ids[0]

        mainObj = MainModel(name='one', value='cheese', other=ids[0])

        mainObj.save(cascadeSave=False)

        assert isinstance(mainObj.other, RefedModel) , 'Expected access of object to return object'

        assert mainObj.other__id == ids[0] , 'Expected __id access to return the object\'s id.'

        mainObj.other = None

        assert not mainObj.other , 'After setting to None, other should be False.'

        ids = mainObj.save()
        assert ids and ids[0] , 'Failed to update'

        fetchedObj = MainModel.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        assert fetchedObj.other == irNull , 'Expected "other" to go back to irNull'



    def test_cascadeFetch(self):
        
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']
        PreMainModel = self.models['PreMainModel']

        refObj = RefedModel(name='rone', strVal='hello', intVal=1)
        ids = refObj.save(cascadeSave=False)
        assert ids and ids[0]

        mainObj = MainModel(name='one', value='cheese', other=ids[0])

        ids = mainObj.save(cascadeSave=False)
        assert ids and ids[0] , 'Failed to save object'

        preMainObj = PreMainModel(name='pone', value='bologna')
        preMainObj.main = mainObj

        ids = preMainObj.save(cascadeSave=False)
        assert ids and ids[0], 'Failed to save object'

        objs = PreMainModel.objects.filter(name='pone').all(cascadeFetch=True)

        assert objs and len(objs) == 1 , 'Failed to fetch single PreMainModel object'

        obj = objs[0]

        oga = object.__getattribute__

        assert oga(obj, 'main').isFetched() is True , 'Expected cascadeFetch to fetch sub object. Failed one level down (not marked isFetched)'

        assert oga(obj, 'main').obj , 'Expected cascadeFetch to fetch sub object. Failed one level down (object not present)'

        fetchedMainObj = oga(obj, 'main').obj

        assert fetchedMainObj == mainObj , 'Fetched MainModel object has wrong values.\n\nExpected: %s\n\nGot:     %s\n' %(repr(mainObj), repr(fetchedMainObj))

        assert oga(fetchedMainObj, 'other').isFetched() is True , 'Expected cascadeFetch to fetch sub object. Failed two levels down (not marked isFetched)'
        assert oga(fetchedMainObj, 'other').obj , 'Expected cascadeFetch to fetch sub object. Failed to levels down (object not present)'

        assert oga(fetchedMainObj, 'other').obj.name == 'rone' , 'Missing values on two-level-down fetched object.'

        MainModel.deleter.destroyModel()
        RefedModel.deleter.destroyModel()
        PreMainModel.deleter.destroyModel()

        # Now test that cascadeFetch=False does NOT fetch the subs.
        refObj = RefedModel(name='rone', strVal='hello', intVal=1)
        ids = refObj.save(cascadeSave=False)
        assert ids and ids[0]

        mainObj = MainModel(name='one', value='cheese', other=ids[0])

        ids = mainObj.save(cascadeSave=False)
        assert ids and ids[0] , 'Failed to save object'

        preMainObj = PreMainModel(name='pone', value='bologna')
        preMainObj.main = mainObj

        ids = preMainObj.save(cascadeSave=False)
        assert ids and ids[0], 'Failed to save object'

        objs = PreMainModel.objects.filter(name='pone').all(cascadeFetch=False)

        assert objs and len(objs) == 1 , 'Failed to fetch objects'

        obj = objs[0]

        assert oga(obj, 'main').isFetched() is False , 'Expected cascadeFetch=False to NOT automatically fetch sub object. isFetched is marked True one level down.'
        assert not bool(oga(obj, 'main').obj) , 'Expected cascadeFetch=False to NOT automatically fetch sub object. Object was found on sub object one level down.'


        # Now try the IndexedRedisModel.cascadeFetch function to perform the fetch.
        objs = PreMainModel.objects.filter(name='pone').all(cascadeFetch=False)

        assert objs and len(objs) == 1 , 'Failed to fetch objects'

        obj = objs[0]
        obj.cascadeFetch()

        assert oga(obj, 'main').isFetched() is True , 'Expected Model.cascadeFetch to fetch sub object. Failed one level down (not marked isFetched)'

        assert oga(obj, 'main').obj , 'Expected Model.cascadeFetch to fetch sub object. Failed one level down (object not present)'

        mainObj = oga(obj, 'main').obj

        assert oga(mainObj, 'other').isFetched() is True , 'Expected Model.cascadeFetch to fetch sub object. Failed two levels down (not marked isFetched)'
        assert oga(mainObj, 'other').obj , 'Expected Model.cascadeFetch to fetch sub object. Failed to levels down (object not present)'

        assert oga(mainObj, 'other').obj.name == 'rone' , 'Missing values on two-level-down fetched object.'




    def test_assign(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)
        refObj2 = RefedModel(name='rtwo', strVal='world', intVal=2)

        ids1 = refObj1.save(cascadeSave=False)
        assert ids1 and ids1[0] , 'Failed to save object'

        ids2 = refObj2.save(cascadeSave=False)
        assert ids2 and ids2[0] , 'Failed to save object'

        mainObj = MainModel(name='one', value='cheese', other=ids1[0])

        assert mainObj.other.hasSameValues(refObj1) , 'Expected other with id of refObj1 to link to refObj1'

        mainObj.other = ids2[0]

        assert mainObj.other.hasSameValues(refObj2) , 'Expected other with id of refObj2 to link to refObj2'

        ids = mainObj.save(cascadeSave=False)
        assert ids and ids[0] , 'Failed to save object'

        fetchedObj = mainObj.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        assert fetchedObj.other__id == ids2[0] , 'Expected __id access to return the object\'s id.'


        mainObj = fetchedObj

        firstRefObj = RefedModel.objects.filter(name='rone').first()

        assert firstRefObj , 'Failed to fetch object'

        mainObj.other = firstRefObj

        ids = mainObj.save(cascadeSave=False)
        assert ids and ids[0] , 'Failed to save'

        fetchedObj = mainObj.objects.filter(name='one').first()

        assert fetchedObj , 'Failed to fetch object'

        assert fetchedObj.other__id == ids1[0] , 'Expected save using Model object would work properly. Did not fetch correct id after save.'
        
    def test_filterOnModel(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)
        refObj2 = RefedModel(name='rtwo', strVal='world', intVal=2)

        ids1 = refObj1.save(cascadeSave=False)
        assert ids1 and ids1[0] , 'Failed to save object'

        ids2 = refObj2.save(cascadeSave=False)
        assert ids2 and ids2[0] , 'Failed to save object'

        mainObj = MainModel(name='one', value='cheese', other=ids1[0])

        assert object.__getattribute__(mainObj, 'other').isFetched() is False , 'Expected object not to be fetched before access'

        assert mainObj.other.hasSameValues(refObj1) , 'Expected other with id of refObj1 to link to refObj1'

        assert object.__getattribute__(mainObj, 'other').isFetched() is True, 'Expected object to be fetched after access'
        mainObj.other = ids2[0]

        assert mainObj.other.hasSameValues(refObj2) , 'Expected other with id of refObj2 to link to refObj2'

        ids = mainObj.save(cascadeSave=False)

        fetchedObjs = MainModel.objects.filter(other=ids2[0]).all()

        assert fetchedObjs and len(fetchedObjs) == 1 , 'Expected to be able to filter on numeric pk'

        fetchedObjs = MainModel.objects.filter(other=refObj2).all()

        assert fetchedObjs and len(fetchedObjs) == 1 , 'Expected to be able to filter on object itself'



    def test_cascadeSave(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']
        PreMainModel = self.models['PreMainModel']

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)

        mainObj = MainModel(name='one', value='cheese')

        mainObj.other = refObj1

        ids = mainObj.save(cascadeSave=True)

        assert ids and ids[0] , 'Failed to save object'

        assert mainObj.other._id , 'Failed to set id on other object'

        obj = MainModel.objects.filter(name='one').first()

        assert obj , 'Failed to fetch object by name'

        assert obj.other , 'Did not cascade save second object and link to parent'

        assert obj.other.name == 'rone' , 'Did save values on cascaded object'

        RefedModel.deleter.destroyModel()
        MainModel.deleter.destroyModel()

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)
        mainObj = MainModel(name='one', value='cheese')

        mainObj.other = refObj1

        preMainObj = PreMainModel(name='pone', value='bologna')

        preMainObj.main = mainObj

        ids = preMainObj.save(cascadeSave=True)

        assert ids and ids[0] , 'Failed to save object'


        obj = PreMainModel.objects.filter(name='pone').first()

        assert obj , 'Failed to fetch object by name'

        assert obj.main , 'Failed to link one level down'
        assert obj.main.name == 'one' , 'Did not save values one level down'

        assert obj.main.other , 'Failed to link two levels down'
        assert obj.main.other.name == 'rone' , 'Failed to save values two levels down'


    def test_reload(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']
        PreMainModel = self.models['PreMainModel']

        oga = object.__getattribute__

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)
        refObj2 = RefedModel(name='rtwo', strVal='hello', intVal=2)

        refObj2.save()

        mainObj = MainModel(name='one', value='cheese')

        mainObj.other = refObj1

        ids = mainObj.save(cascadeSave=True)

        assert ids and ids[0] , 'Failed to save object'

#        mainObj = MainModel.objects.first()

        robj = RefedModel.objects.filter(name='rone').first()

        robj.intVal = 5
        ids = robj.save()
        assert ids and ids[0] , 'Failed to save object'

        mainObj.reload(cascadeObjects=False)

        assert mainObj.other.intVal != 5 , 'Expected reload(cascadeObjects=False) to NOT reload sub-object'

        mainObj.reload(cascadeObjects=True)
        
        assert mainObj.other.intVal == 5 , 'Expected reload(cascadeObjects=True) to reload sub-object'

        mainObj = MainModel.objects.first()

        assert oga(mainObj, 'other').isFetched() is False , 'Expected sub-obj to not be fetched automatically'

        z = mainObj.asDict(forStorage=False)

        assert oga(mainObj, 'other').isFetched() is False , 'Expected calling "asDict" to not fetch foreign object'

        reloadedData = mainObj.reload(cascadeObjects=False)

        assert oga(mainObj, 'other').isFetched() is False , 'Expected reload(cascadeObjects=False) to not fetch sub-object'

        assert not reloadedData , 'Expected no data to be reloaded'

        reloadedData = mainObj.reload(cascadeObjects=True)

        assert oga(mainObj, 'other').isFetched() is False , 'Expected reload(cascadeObjects=True) to not fetch sub-object'

        assert not reloadedData , 'Expected no data to be reloaded'

        mainObj.other

        assert oga(mainObj, 'other').isFetched() is True , 'Expected access to fetch sub object'

        reloadedData = mainObj.reload(cascadeObjects=False)

        assert not reloadedData , 'Expected no data to be reloaded with local resolved but unchanged.'

        mainObj.other.intVal = 99

        reloadedData = mainObj.reload(cascadeObjects=False)

        assert not reloadedData , 'Expected to not see "other" in reloaded data, as pk did not change but values did.'

        reloadedData = mainObj.reload(cascadeObjects=True)

        assert 'other' in reloadedData , 'Expected "other" to  be reloaded with reload(cascadeObjects=True)'

        assert reloadedData['other'][0].getObj().intVal == 99 , 'Expected old value to be present in reload'

        assert reloadedData['other'][1].getObj().intVal == 5 , 'Expected new value to be present in reload'


        mainObj = MainModel.objects.first()

        mainObj.other = refObj2._id

        reloadedData = mainObj.reload(cascadeObjects=False)
        
        assert 'other' in reloadedData , 'Expected to see "other" in reloaded data when cascadeObjects=False when pk changes. Using pk assignment.'

        mainObj = MainModel.objects.first()

        mainObj.other = refObj2._id
        reloadedData = mainObj.reload(cascadeObjects=True)
        
        assert 'other' in reloadedData , 'Expected to see "other" in reloaded data when cascadeObjects=True when pk changes. Using pk assignment.'


        mainObj = MainModel.objects.first()

        mainObj.other = refObj2

        reloadedData = mainObj.reload(cascadeObjects=False)
        assert 'other' in reloadedData , 'Expected to see "other" in reloaded data when cascadeObjects=False when pk changes. Using obj assignment.'

        mainObj = MainModel.objects.first()

        mainObj.other = refObj2

        reloadedData = mainObj.reload(cascadeObjects=True)
        assert 'other' in reloadedData , 'Expected to see "other" in reloaded data when cascadeObjects=True when pk changes. Using obj assignment.'

        preMainObj = PreMainModel(name='pone', value='zzz')

        preMainObj.main = mainObj._id

        preMainObj.save()


        preMainObj = PreMainModel.objects.filter(name='pone').first()

        assert preMainObj , 'Failed to fetch object'

        preMainObj.main.other.intVal = 33
        reloadedData = preMainObj.reload(cascadeObjects=False)
        assert not reloadedData , 'Expected to not see any reloaded data for cascadeObjects=False when object two-levels-down has changed values.'

        reloadedData = preMainObj.reload(cascadeObjects=True)
        assert 'main' in reloadedData , 'Expected to see "main" (one-level-down) object show up in reloaded data for cascadeObjects=True when object two-levels-down has changed values.'



    def test_suppressFetching(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        oga = object.__getattribute__

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)

        mainObj = MainModel(name='one', value='cheese')

        mainObj.other = refObj1

        ids = mainObj.save(cascadeSave=True)

        assert ids and ids[0] , 'Failed to save object'

        mainObj = MainModel.objects.first()

        assert oga(mainObj, 'other').isFetched() is False , 'Expected other to not be fetched right away'

        updatedFields = mainObj.getUpdatedFields()

        assert not updatedFields , 'Expected updatedFields to be blank. Got: %s' %(repr(updatedFields), )

        assert oga(mainObj, 'other').isFetched() is False , 'Expected other to not be fetched after calling getUpdatedFields'


    def test_unsavedChanges(self):
        MainModel = self.models['MainModel']
        RefedModel = self.models['RefedModel']

        oga = object.__getattribute__

        refObj1 = RefedModel(name='rone', strVal='hello', intVal=1)

        mainObj = MainModel(name='one', value='cheese')

        mainObj.other = refObj1

        ids = mainObj.save(cascadeSave=True)

        mainObj2 = MainModel(name='one', value='cheese')

        assert mainObj.hasSameValues(mainObj2) is False , 'Expected not to have same values when one has foreign set, other does not.'


        mainObj2.other = refObj1._id

        assert mainObj.hasSameValues(mainObj2) , 'Expected to have same values when one has object, other has id'

        mainObj2 = MainModel(name='one', value='cheese')
        mainObj2.other = refObj1

        assert mainObj.hasSameValues(mainObj2) , 'Expected to have same values with same object on both'

        mainObj = MainModel.objects.first()

        assert mainObj.hasSameValues(mainObj2) , 'Expected to have same values after fetch. one has id, one has object.'

        mainObj.other.intVal = 55

        assert not mainObj.hasSameValues(mainObj2) , 'Expected changing a foreign link field\'s data on one object would cause hasSameValues to be False.'

        assert mainObj.hasSameValues(mainObj2, cascadeObject=False) , 'Expected changing a foreign link field\'s data on one object would leave hasSameValues(... , cascadeObject=False) to be True'


if __name__ == '__main__':
    sys.exit(subprocess.Popen('GoodTests.py -n1 "%s" %s' %(sys.argv[0], ' '.join(['"%s"' %(arg.replace('"', '\\"'), ) for arg in sys.argv[1:]]) ), shell=True).wait())

# vim: set ts=4 sw=4 expandtab
