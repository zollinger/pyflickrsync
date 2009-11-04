#! /usr/bin/env python

import flickrapi
import os,sys,fnmatch
import hashlib
import getopt


class FlickrSync:
    img_pattern = "*.jpg"
    flickr = False
    base_dir = False
    current_photo = False
    photo_queue = False
    CONFIG_DIR = '.flickrsync'
    api_key = False
    api_secret = False
    photo_is_family = 0
    photo_is_friend = 0
    photo_is_public = 0
    photo_sets = []
    verbose = False
    def __init__(self, api_key, api_secret, img_dir):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_dir = img_dir
        
       
        
    def start(self):
        
        self.flickr = flickrapi.FlickrAPI(self.api_key, self.api_secret)
        (token, frob) = self.flickr.get_token_part_one(perms='write')
        if not token: raw_input("Press ENTER after you authorized this program")
        self.flickr.get_token_part_two((token, frob))
        print 'Setting up directory'
        self.setup_dir()
        print 'Getting existing flickr sets'
        self.get_existing_sets()
        print 'Looking for files'
        self.photo_queue =  self.get_images_generator()
        print 'Starting...'
        self.process()
        
    def get_existing_sets(self):
        '''Gets existing sets from Flickr''' 
        sets = self.flickr.photosets_getList()
        for set in sets.find('photosets').findall('photoset'):
            self.photo_sets.append({'name': set[0].text, 'id': set.attrib['id'] })
           
        print self.photo_sets
        
    def setup_dir(self):
        '''Setup configuration directory where we store which images 
        have been uploaded already.'''
        try:
            if not os.path.exists(os.path.join(self.base_dir, self.CONFIG_DIR)):
                os.mkdir(os.path.join(self.base_dir, self.CONFIG_DIR))
        except:
            print "Could not create configuration directory"
            sys.exit(1)

    def get_images_generator(self):
        '''Locate all files matching supplied filename pattern in and below
        supplied root directory.'''
        for path, dirs, files in os.walk(self.base_dir):
            for filename in fnmatch.filter(files, self.img_pattern):
                yield Photo(os.path.join(path, filename))
    
    def process(self):
        try:
            
            self.current_photo = self.photo_queue.next()
            if self.photo_is_uploaded(self.current_photo):
                print "Skipping ", self.current_photo.path
                self.process()
            else:
                self.upload_current()
        except StopIteration:
            pass
    
    def photo_is_uploaded(self, photo):
        if os.path.exists(os.path.join(self.base_dir, self.CONFIG_DIR, photo.hash())):
            return True
        return False
    
    def get_set_name(self, setname, photo_id):
        '''Tries to find an existing set name or creates a new one and returns id'''
        # 
        #self.flickr.photosets_create(title='Test set 2', primary_photo_id='4069933472')
        # res2.find('photoset').attrib['id'] get photoset id of created set
        for set in self.photo_sets:
            if set['name'] == setname:
                return set['id']
        print 'Creating new set ', setname
        resp = self.flickr.photosets_create(title=setname, primary_photo_id=photo_id)
        new_set_id = resp.find('photoset').attrib['id']
        self.photo_sets.append({'name': setname, 'id': new_set_id })
        return new_set_id
        
        
    def photo_set_uploaded(self, photo):
        file_path = os.path.join(self.base_dir, self.CONFIG_DIR, photo.hash())
        if not os.path.exists(file_path):
            open(file_path, 'w').close()
    
    def upload_current(self):
        tags = self.current_photo.path.replace(self.base_dir, '').split('/')[:-1]
        image_tags = '"' + '" "'.join( tags )+ '"'
        print "Start uploading ", self.current_photo.path
        print "Tags: ", image_tags
        
        response =  self.flickr.upload(filename=self.current_photo.path, callback=None, \
                            tags=image_tags, is_family=self.photo_is_family, \
                            is_public=self.photo_is_public, is_friend=self.photo_is_friend, format='etree')
        new_photo_id =  response.findall('photoid')[0].text
        # Find set id and add photo
        if len(tags) > 0:
            set_id = self.get_set_name(tags[0], new_photo_id)
            try:
                print 'Adding photo to set', set_id
                self.flickr.photosets_addPhoto(photoset_id=set_id, photo_id=new_photo_id)
            except:
                print 'Photo already in set'
        
        self.photo_set_uploaded(self.current_photo)
        self.process()
        
    def cb(self, progress, done):
        if done:
            pass
        else:
            if self.verbose:
                print "At %s%%" % progress
            

class Photo:
    _hash = False
    path = False
    def __init__(self, path):
        self.path = path
    
    def hash(self):
        if not self._hash:
            m = hashlib.md5()
            m.update(open(self.path, 'rb').read())
            self._hash = m.hexdigest()
        return self._hash


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help", "api_key=", "secret=", "dir="])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    api_key = False
    secret = False
    dir = False
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-a", "--api_key"):
            api_key = a
        elif o in ("-s", "--secret"):
            secret = a
        elif o in ("-d", "--dir"):
            dir = a
        else:
            assert False, "unhandled option"
        
    if not api_key or not secret or not dir:
        print "Invalid options"
        usage()
        sys.exit(2)
    try:
        f = FlickrSync(api_key, secret, dir)
        f.verbose = verbose
        f.start()
    except KeyboardInterrupt:
        sys.exit(0)


def usage():
    print "Usage: python flickrsync.py --api_key=XXXX --secret=XXXX --dir=/my/photo/library/ [-v]"
    print "--api_key    API key from your flickr account"
    print "--secret    Your apps secret key"
    print "--dir    Base directory of your photo library"

if __name__ == '__main__':
    main()
        

    