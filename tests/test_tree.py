# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-11-29 10:28:58
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-07-27 17:22:02

from __future__ import print_function, division, absolute_import
import pytest
from tree import config
from tree.tree import Tree, get_envvar_history, get_path_history
import six
import os


@pytest.fixture()
def tree():
    t = Tree()
    t.replant_tree()
    yield t
    t = None


class TestTree(object):

    def test_load(self, tree):
        assert tree.treedir is not None
        assert isinstance(tree.treedir, six.string_types)
        assert tree.environ is not None
        assert 'APO' in tree.environ
        assert 'sdsswork' == tree.environ['default']['name']

    @pytest.mark.parametrize('keys', [('manga'), ('MANGA'), (['manga', 'apogee'])],
                             ids=['manga', 'capmanga', 'apomanga'])
    def test_load_keys(self, keys):
        t = Tree(key=keys)
        assert 'APO' not in t.environ
        assert 'default' in t.environ
        assert 'general' in t.environ
        keys = keys if isinstance(keys, list) else [keys]
        for key in keys:
            assert key.upper() in t.environ

    @pytest.mark.parametrize('dr', [('dr15')])
    def test_load_dr_config(self, dr):
        t = Tree(config=dr)
        assert dr == t.environ['default']['name']

    def _assert_paths(self, tree, dr=None):
        assert 'MANGA_SPECTRO_REDUX' in tree.environ['MANGA']
        assert 'MANGA_SPECTRO_ANALYSIS' in tree.environ['MANGA']
        if dr:
            assert dr in tree.environ['default']['name']
            assert dr in tree.environ['MANGA']['MANGA_ROOT']
            assert dr in tree.environ['MANGA']['MANGA_SPECTRO_REDUX']
            assert dr in tree.environ['MANGA']['MANGA_SPECTRO_ANALYSIS']

    @pytest.mark.parametrize('dr', [('dr15')])
    def test_load_with_update(self, tree, dr):
        assert 'sdsswork' in tree.environ['default']['name']
        assert 'mangawork' in tree.environ['MANGA']['MANGA_ROOT']
        tree = Tree(config=dr, update=True)
        self._assert_paths(tree, dr=dr)

    @pytest.mark.parametrize('dr', [('dr15')])
    def test_replant_tree(self, tree, dr):
        assert 'sdsswork' in tree.environ['default']['name']
        assert 'mangawork' in tree.environ['MANGA']['MANGA_ROOT']
        tree.replant_tree(dr)
        self._assert_paths(tree, dr=dr)

    def test_custom_paths_remain(self, monkeypatch):
        # set custom environ variable
        name = 'MANGA_QUICK'
        path = '/tmp/work/manga/quick'
        monkeypatch.setitem(os.environ, name, path)
        assert os.environ[name] == path
        tree = Tree()
        assert os.environ[name] == path
        assert path != tree.environ['MANGA'][name]

    def test_custom_paths_donotupdate(self, monkeypatch, tree):
        name = 'MANGA_QUICK'
        path = '/tmp/work/manga/quick'
        monkeypatch.setitem(os.environ, name, path)
        assert os.environ[name] == path
        tree.replant_tree('sdsswork')
        assert os.environ[name] != path
        assert os.environ[name] == tree.environ['MANGA'][name]

    def test_custom_paths_update_with_exclude(self, monkeypatch, tree):
        name = 'MANGA_QUICK'
        path = '/tmp/work/manga/quick'
        monkeypatch.setitem(os.environ, name, path)
        assert os.environ[name] == path
        tree.replant_tree('sdsswork', exclude=['MANGA_QUICK'])
        assert os.environ[name] == path
        assert path != tree.environ['MANGA'][name]

    def test_paths(self, tree):
        assert 'PATHS' not in tree.environ
        assert tree.paths is not None
        assert isinstance(tree.paths, dict)

    def test_get_orig_os(self, tree):
        # need to check if on system with no sdsswork modules running (i.e. Travis)
        orig_os = tree.get_orig_os_environ()
        hassas = orig_os.get("SAS_ROOT", None)
        if hassas:
            assert 'mangawork' in orig_os.get("MANGA_ROOT")
        else:
            assert 'MANGA_ROOT' not in orig_os

        assert 'mangawork' in os.getenv("MANGA_ROOT")
        tree.replant_tree('dr15')
        if hassas:
            assert 'dr15' not in orig_os.get("MANGA_ROOT")
        else:
            assert 'MANGA_ROOT' not in orig_os
        assert 'dr15' in os.getenv("MANGA_ROOT")

    def test_reset_orig_os(self, tree):
        # need to check if on system with no sdsswork modules running (i.e. Travis)
        orig_os = tree.get_orig_os_environ()
        hassas = orig_os.get("SAS_ROOT", None)
        tree.replant_tree('dr15')
        assert 'dr15' in os.getenv("MANGA_ROOT")
        tree.reset_os_environ()
        if hassas:
            assert 'mangawork' in os.getenv("MANGA_ROOT")
        else:
            assert "MANGA_ROOT" not in os.environ

    def test_list_configs(self, tree):
        cfgs = tree.list_available_configs()
        assert 'dr15.cfg' in cfgs

    @pytest.mark.parametrize('public', [(True), (False)])
    def test_get_releases(self, tree, public):
        rels = tree.get_available_releases(public=public)
        assert 'DR15' in rels
        if public:
            assert 'WORK' not in rels
        else:
            assert 'WORK' in rels

    @pytest.mark.parametrize('config, release',
                             [('sdsswork', 'WORK'),
                              ('mpl8', 'MPL8'),
                              ('sdss5', 'WORK'),
                              ('dr15', 'DR15')])
    def test_config_to_release(self, config, release):
        tree = Tree(config)
        assert tree.config_name == config
        assert tree.release == release

    @pytest.mark.parametrize('collapse', [(True), (False)])
    def test_to_dict(self, tree, collapse):
        envdict = tree.to_dict(collapse=collapse)
        if collapse:
            assert 'MANGA' not in envdict
            assert 'MANGA_ROOT' in envdict
        else:
            assert 'MANGA' in envdict
            assert 'MANGA_ROOT' not in envdict
            assert 'MANGA_ROOT' in envdict['MANGA']

    def test_set_product_root(self, tmp_path, tree):
        temp_prod = tmp_path / 'software'
        temp_prod.mkdir()
        tree.set_product_root(root=str(temp_prod))
        assert tree.productroot_dir == str(temp_prod)
        assert os.getenv("PRODUCT_ROOT") == str(temp_prod)

    def test_write_old_paths(self, faketree):

        tree = Tree()

        pathsfile = os.path.join(tree.treedir, 'data/sdss_paths.ini')
        assert not os.path.exists(pathsfile)

        tree.write_old_paths_inifile()

        assert os.path.exists(pathsfile)
        assert os.path.isfile(pathsfile)

    def assert_orig_sdss5_envvars(self):
        assert os.getenv("ROBOSTRATEGY_DATA") == '/tmp/robodata'
        assert os.getenv("ALLWISE_DIR") == '/tmp/allwise'
        assert os.getenv("EROSITA_DIR") == '/tmp/erosita'

    def assert_all_envvars(self):
        self.assert_orig_sdss5_envvars()
        assert 'sdsswork/sandbox/robostrategy' not in os.getenv("ROBOSTRATEGY_DATA")

    def assert_subset_envvars(self):
        assert 'sdsswork/sandbox/robostrategy' in os.getenv("ROBOSTRATEGY_DATA")
        assert os.getenv("ROBOSTRATEGY_DATA") != '/tmp/robodata'
        assert os.getenv("ALLWISE_DIR") == '/tmp/allwise'
        assert os.getenv("EROSITA_DIR") == '/tmp/erosita'

    def test_plant_no_update(self, monkeysdss5):
        self.assert_orig_sdss5_envvars()
        tree = Tree(config='sdss5')
        self.assert_orig_sdss5_envvars()

    def test_replant_update(self, monkeysdss5):
        self.assert_orig_sdss5_envvars()
        tree = Tree(config='sdsswork')
        self.assert_orig_sdss5_envvars()
        tree.replant_tree('sdss5')

        assert 'sdsswork/sandbox/robostrategy' in os.getenv("ROBOSTRATEGY_DATA")
        assert 'sdsswork/target/catalogs/allwise' in os.getenv("ALLWISE_DIR")
        assert 'sdsswork/target/catalogs/eRosita' in os.getenv("EROSITA_DIR")

    def test_replant_preserve_all_envvars(self, monkeysdss5):
        self.assert_orig_sdss5_envvars()
        tree = Tree(config='sdsswork')
        tree.replant_tree('sdss5', preserve_envvars=True)
        self.assert_all_envvars()

    def test_replant_preserve_subset_envvars(self, monkeysdss5):
        self.assert_orig_sdss5_envvars()
        tree = Tree(config='sdsswork')
        tree.replant_tree('sdss5', preserve_envvars=['ALLWISE_DIR', 'EROSITA_DIR'])
        self.assert_subset_envvars()

    def test_replant_preserve_all_from_config(self, monkeysdss5, monkeypatch):
        monkeypatch.setitem(config, 'preserve_envvars', True)
        self.assert_orig_sdss5_envvars()
        tree = Tree(config='sdsswork')
        tree.replant_tree('sdss5')
        self.assert_all_envvars()

    def test_replant_preserve_subset_from_config(self, monkeysdss5, monkeypatch):
        monkeypatch.setitem(config, 'preserve_envvars', ['ALLWISE_DIR', 'EROSITA_DIR'])
        self.assert_orig_sdss5_envvars()
        tree = Tree(config='sdsswork')
        tree.replant_tree('sdss5')
        self.assert_subset_envvars()

    def test_missing_path_envvars(self, tree):
        # remove an envvar
        tree.environ['MANGA'].pop("MANGA_SWIM")
        missing = tree.check_missing_path_envvars()
        assert "MANGA_SWIM" in missing

    @pytest.mark.parametrize('file, envvar',
                             [('mangawork/manga/spectro/redux/v3_1_1/8485/file.txt', 'MANGA_SPECTRO_REDUX'),
                              ('ebosswork/eboss/file.txt', 'EBOSS_ROOT'),
                              ('file.txt', 'SAS_BASE_DIR'),
                              ('/root/dir/file.txt', None)],
                             ids=['manga', 'eboss', 'sas', 'none'])
    def test_identify_envvar(self, faketree, tree, file, envvar):
        """ test we can identify an envvar from a file """
        path = os.path.join(faketree, file)
        ee = tree.identify_envvar(path)
        assert envvar == ee

    @pytest.mark.parametrize('envvar, sec',
                             [('MANGA_SPECTRO_REDUX', 'MANGA'),
                              ('EBOSS_ROOT', 'EBOSS'),
                              ('SAS_BASE_DIR', 'general'),
                              ('NO_ENVVAR', None)],
                             ids=['manga', 'eboss', 'sas', 'none'])
    def test_identify_section(self, tree, envvar, sec):
        """ test we can identify an ini section from an envvar """
        ss = tree.identify_section(envvar)
        assert sec == ss

    @pytest.mark.parametrize('envvar, sec',
                             [('MANGA_SPECTRO_REDUX', 'MANGA'),
                              ('MANGA_NEWVAC', 'MANGA'),
                              ('EBOSS_JOKER', 'EBOSS'),
                              ('SAS_BASE_DIR', 'general'),
                              ('APOGEE_CRYSTAL', 'APOGEE'),
                              ('APOGEECRYSTAL', 'APOGEE')],
                             ids=['manga1', 'manga2', 'eboss', 'sas', 'apogee1', 'apogee2'])
    def test_identify_section_guess(self, tree, envvar, sec):
        ss = tree.identify_section(envvar, guess=True)
        assert sec == ss


def test_get_path_history():
    im = get_path_history('mangaimage')
    assert im['dr12'] is None
    assert im['dr17'] == '$MANGA_SPECTRO_REDUX/{drpver}/{plate}/images/{ifu}.png'
    assert im['dr16'] == '$MANGA_SPECTRO_REDUX/{drpver}/{plate}/{dir3d}/images/{ifu}.png'


def test_get_envvar_history():
    swim = get_envvar_history('MANGA_SWIM')
    assert swim['dr15'] is None
    assert 'sas/dr16/manga/swim' in swim['dr16']
    assert swim['sdss5'] is None
