import flickrapi
import os,sys,fnmatch
import hashlib

api_key = '3d910dbe5302ff28415039a78520debf'
api_secret = 'e0b09baf3bdd1945'

class FlickrSync:
    img_pattern = "*.jpg"
    flickr = False
    base_dir = False
    current_photo = False
    photo_queue = False
    CONFIG_DIR = '.flickrsync'
    api_key = False
    api_secret = False
    
    def __init__(self, api_key, secret, img_dir):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_dir = img_dir
        
       
        
    def start(self):
        
        self.flickr = flickrapi.FlickrAPI(api_key, api_secret)
        (token, frob) = self.flickr.get_token_part_one(perms='write')
        if not token: raw_input("Press ENTER after you authorized this program")
        self.flickr.get_token_part_two((token, frob))
        
        self.setup_dir()
        self.photo_queue =  self.get_images_generator()
        self.process()
        
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
        
    def photo_set_uploaded(self, photo):
        file_path = os.path.join(self.base_dir, self.CONFIG_DIR, photo.hash())
        if not os.path.exists(file_path):
            open(file_path, 'w').close() 
    
    def upload_current(self):
        image_tags = '"' + '" "'.join( self.current_photo.path.replace(self.base_dir, '').split('/')[:-1] )+ '"'
        print "Start uploading ", self.current_photo.path
        print "Tags: ", image_tags
        
        self.flickr.upload(filename=self.current_photo.path, callback=self.cb, tags=image_tags)
        
    def cb(self, progress, done):
        if done:
            self.photo_set_uploaded(self.current_photo)
            print "Done uploading "
            self.process()
        else:
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
        print self._hash
        return self._hash
    
if __name__ == '__main__':
            
    try:
        f = FlickrSync(api_key, api_secret, '../images/')
        f.start()
    except KeyboardInterrupt:
        sys.exit(0)

    